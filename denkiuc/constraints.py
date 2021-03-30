import pulp as pp


def supply_eq_demand(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            label = 'meet_demand_i_%d_s_%d' % (i, s)

            condition = \
                (
                 pp.lpSum([vars['power_generated'].var[(i, s, u)]
                           for u in sets['units'].indices])
                 + vars['unserved_power'].var[(i, s)]
                 ==
                 data.traces['demand'][(s, 'Demand')][i]
                 + pp.lpSum([vars['charge_after_losses'].var[(i, s, u)]
                             * (1 / data.units['RTEfficiency'][u])
                             for u in sets['units_storage'].indices])
                 )

            mod += condition, label
    return mod


def meet_reserve_requirement(sets, data, vars, mod):
    for r in sets['reserves'].indices:
        for i in sets['intervals'].indices:
            for s in sets['scenarios'].indices:
                label = 'meet_reserve_requirement_i_%d_s_%d_r_%s' % (i, s, r)
                condition = \
                    (
                     pp.lpSum([vars['reserve_enabled'].var[(i, s, u, r)]
                               for u in sets['units'].indices])
                     + vars['unserved_reserve'].var[(i, s, r)]
                     >=
                     data.reserve_requirement[r][i]
                     )

                mod += condition, label

    return mod


def intermittent_resource_availability(sets, data, vars, mod):
    import denkiuc.misc_functions as mf

    for u in sets['units_variable'].indices:
        region = data.units['Region'][u]
        technology = data.units['Technology'][u]

        for s in sets['scenarios'].indices:
            trace = mf.get_resource_trace(s, region, technology, data)
            for i in sets['intervals'].indices:
                label = 'variable_resource_availability_u_%s_i_%d_s_%d' % (u, i, s)

                condition = \
                    (
                     vars['power_generated'].var[(i, s, u)]
                     <= trace[i] * data.units['Capacity_MW'][u]
                    )

                mod += condition, label

    return mod


def commitment_continuity(sets, data, vars, mod):
    for i in sets['intervals'].indices:

        for u in sets['units_commit'].indices:
            if i == min(sets['intervals'].indices):
                for s in sets['scenarios'].indices:
                    label = 'commitment_continuity_%s_int_%s' % (u, i)

                    condition = \
                        (
                         vars['num_commited'].var[(i, s, u)]
                         ==
                         data.initial_state['NumCommited'][u]
                         + vars['num_starting_up'].var[(i, s, u)]
                         - vars['num_shutting_down'].var[(i, s, u)]
                         )

                if i > min(sets['intervals'].indices):
                    label = 'commitment_continuity_%s_int_%s' % (u, i)

                    condition = \
                        (
                         vars['num_commited'].var[(i, s, u)]
                         ==
                         vars['num_commited'].var[(i-1, s, u)]
                         + vars['num_starting_up'].var[(i, s, u)]
                         - vars['num_shutting_down'].var[(i, s, u)]
                         )

                mod += condition, label

    return mod


def inflexible_commitment(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_inflexible'].indices:
                label = 'inflexible_commit_same_across_scenarios_u_%s_i_%s_s_%s' % (u, s, i)
                condition = \
                    (
                     vars['num_commited'].var[(i, s, u)]
                     ==
                     vars['num_committed_all_scenarios'].var[(i, u)]
                     )

            mod += condition, label

    return mod


def max_units_committed(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'num_units_commit_lt_exist_%s_int_%s_s_%d' % (u, i, s)

                condition = \
                    (vars['num_commited'].var[(i, s, u)]
                     <=
                     data.units['NoUnits'][u])

                mod += condition, label

    return mod


def power_lt_committed_capacity(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'power_lt_commited_cap_%s_int_%s_s_%s' % (u, i, s)

                condition = \
                    (vars['power_generated'].var[(i, s, u)]
                     + pp.lpSum(vars['reserve_enabled'].var[(i, s, u, r)]
                                for r in sets['raise_reserves'].indices)
                     <=
                     vars['num_commited'].var[(i, s, u)] * data.units['Capacity_MW'][u])

                mod += condition, label
    return mod


def power_gt_min_stable_gen(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'power_gt_min_stable_gen_%s_int_%s_s_%s' % (u, i, s)

                condition = \
                    (vars['power_generated'].var[(i, s, u)]
                     - pp.lpSum(vars['reserve_enabled'].var[(i, s, u, r)]
                                for r in sets['lower_reserves'].indices)
                     >=
                     vars['num_commited'].var[(i, s, u)]
                     * data.units['Capacity_MW'][u]
                     * data.units['MinGen'][u])

                mod += condition, label
    return mod


def power_lt_capacity(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units'].indices:
                label = 'power_lt_cap_%s_i_%d_s_%d' % (u, i, s)

                condition = \
                    (vars['power_generated'].var[(i, s, u)]
                     + pp.lpSum(vars['reserve_enabled'].var[(i, s, u, r)]
                                for r in sets['raise_reserves'].indices)
                     <=
                     data.units['Capacity_MW'][u] * data.units['NoUnits'][u]
                     )

                mod += condition, label
    return mod


def minimum_up_time(sets, data, vars, mod, settings):
    i0 = min(sets['intervals'].indices)

    for i in sets['intervals'].indices:
        i_high = i + 1

        for u in sets['units_commit'].indices:
            unit_up_time = data.units['MinUpTime_h'][u]
            i_low = 1 + max(i0 - 1, i - settings['INTERVALS_PER_HOUR'] * unit_up_time)
            for s in sets['scenarios'].indices:
                label = 'minimum_up_time_i_%d_u_%s_s_%d' % (i, u, s)
                condition = (
                    vars['num_commited'].var[(i, s, u)]
                    >=
                    pp.lpSum([vars['num_starting_up'].var[(i2, s, u)]
                              for i2 in range(i_low, i_high)])
                    )

                mod += condition, label

    return mod


def minimum_down_time(sets, data, vars, mod, settings):
    i0 = min(sets['intervals'].indices)

    for i in sets['intervals'].indices:
        i_high = i + 1

        for u in sets['units_commit'].indices:
            unit_down_time = data.units['MinDownTime_h'][u]
            if i - i0 <= unit_down_time:
                pass

            i_low = 1 + max(i0 - 1, i - settings['INTERVALS_PER_HOUR'] * unit_down_time)
            for s in sets['scenarios'].indices:
                label = 'minimum_down_time_i_%d_u_%s_s_%d' % (i, u, s)
                condition = (
                    data.units['NoUnits'][u] - vars['num_commited'].var[(i, s, u)]
                    >=
                    pp.lpSum([vars['num_shutting_down'].var[(i2, s, u)]
                              for i2 in range(i_low, i_high)])
                    )

                mod += condition, label

    return mod


def energy_storage_continuity(sets, data, vars, mod, settings):
    for i in sets['intervals'].indices:
        if i > min(sets['intervals'].indices):
            for s in sets['scenarios'].indices:
                for u in sets['units_storage'].indices:
                    label = 'storage_continuity_%s_int_%d_s_%d' % (u, i, s)

                    condition = \
                        (vars['energy_in_reservoir'].var[(i, s, u)]
                         ==
                         vars['energy_in_reservoir'].var[(i-1, s, u)]
                         + vars['charge_after_losses'].var[(i, s, u)]
                         * (1 / settings['INTERVALS_PER_HOUR'])
                         - vars['power_generated'].var[(i, s, u)]
                         * (1 / settings['INTERVALS_PER_HOUR'])
                         )
                    mod += condition, label
    return mod


def energy_storage_continuity_first_interval(sets, data, vars, mod, settings):
    for s in sets['scenarios'].indices:
        for u in sets['units_storage'].indices:
            i = min(sets['intervals'].indices)
            initial_energy_in_reservoir \
                = (data.initial_state['StorageLevel_frac'][u]
                   * data.units['StorageCap_h'][u]
                   * data.units['Capacity_MW'][u])
            label = 'storage_continuity_%s_int_%d_s%d' % (u, i, s)
            condition = \
                (vars['energy_in_reservoir'].var[(i, s, u)]
                 ==
                 initial_energy_in_reservoir
                 + vars['charge_after_losses'].var[(i, s, u)]
                 * (1 / settings['INTERVALS_PER_HOUR'])
                 - vars['power_generated'].var[(i, s, u)] * (1 / settings['INTERVALS_PER_HOUR']))
            mod += condition, label
    return mod


def max_stored_energy(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_storage'].indices:
                label = 'max_stored_energy_%s_int_%s_s_%s' % (u, i, s)

                condition = \
                    (
                     vars['energy_in_reservoir'].var[(i, s, u)]
                     <=
                     data.units['StorageCap_h'][u] * data.units['Capacity_MW'][u]
                    )

                mod += condition, label
    return mod


def max_charge(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_storage'].indices:
                label = 'max_charge_%s_int_%d_s%d' % (u, i, s)
                condition = \
                    (vars['charge_after_losses'].var[(i, s, u)]
                     <=
                     data.units['RTEfficiency'][u]
                     * data.units['Capacity_MW'][u])
                mod += condition, label

    return mod


def maximum_reserve_enablement(sets, data, vars, mod):
    import denkiuc.misc_functions as mf

    for u in sets['units'].indices:
        if u in sets['units_commit'].indices:
            for r in sets['reserves'].indices:
                max_reserves_per_unit = mf.get_max_reserves_per_unit(u, r, data.units)

                for i in sets['intervals'].indices:
                    for s in sets['scenarios'].indices:
                        label = 'maximum_reserves_enabled_i_%d_s_%s_u_%s_r_%s' % (i, s, u, r)
                        condition = (
                            vars['reserve_enabled'].var[(i, s, u, r)]
                            <=
                            vars['num_commited'].var[(i, s, u)] * max_reserves_per_unit
                            )
                        mod += condition, label

        else:
            for r in sets['reserves'].indices:
                max_reserves_per_unit = mf.get_max_reserves_per_unit(u, r, data.units)

                for i in sets['intervals'].indices:
                    for s in sets['scenarios'].indices:
                        label = 'maximum_reserves_enabled_i_%d_s_%s_u_%s_r_%s' % (i, s, u, r)
                        condition = (
                            vars['reserve_enabled'].var[(i, s, u, r)]
                            <=
                            data.units['NoUnits'][u] * max_reserves_per_unit
                            )

                        mod += condition, label

    return mod


def limit_rocof(sets, data, vars, mod, settings):
    import denkiuc.misc_functions as mf

    def define_rocof_condition(settings, contingency_size, available_inertia):
        condition = \
            (
             2 * settings['MAX_ROCOF'] * available_inertia
             >=
             contingency_size * settings['SYSTEM_FREQUENCY']
            )

        return condition

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            system_inertia = \
                pp.lpSum(vars['num_commited'].var[(i, s, u2)]
                         * data.units['InertialConst_s'][u2]
                         * data.units['Capacity_MW'][u2]
                         for u2 in sets['units_commit'].indices)

            for u in sets['units'].indices:
                label = 'limit_rocof_%s_int_%d_s_%d' % (u, i, s)

                if u in sets['units_commit'].indices:
                    units_inertia = \
                        vars['num_commited'].var[(i, s, u)] \
                        * data.units['InertialConst_s'][u] \
                        * data.units['Capacity_MW'][u]

                    contingency_size = \
                        vars['is_committed'].var[(i, s, u)] * data.units['Capacity_MW'][u]

                elif u in sets['units_variable'].indices:
                    units_inertia = 0
                    technology = data.units['Technology'][u]
                    region = data.units['Region'][u]
                    trace = mf.get_resource_trace(s, region, technology, data)
                    contingency_size = trace[i] * data.units['Capacity_MW'][u]

                elif u in sets['units_storage'].indices:
                    units_inertia = 0
                    contingency_size = data.units['Capacity_MW'][u]

                available_inertia = system_inertia - units_inertia

                condition = define_rocof_condition(settings, contingency_size, available_inertia)

                mod += condition, label

    return mod


def define_is_committed(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'define_is_committed_%s_int_%d_s_%d' % (u, i, s)

                condition = \
                    (
                     vars['num_commited'].var[(i, s, u)]
                     <=
                     vars['is_committed'].var[(i, s, u)] * data.units['NoUnits'][u]
                    )

                mod += condition, label

    return mod


def create_constraints_df(path_to_inputs):
    import os
    import pandas as pd

    constraints_df = pd.read_csv(os.path.join(path_to_inputs, 'constraints.csv'), index_col=0)
    return constraints_df


def add_all_constraints_to_dataframe(sets, data, vars, settings, mod, constraints_df):
    if constraints_df['Include']['supply_eq_demand'] == 1:
        mod = supply_eq_demand(sets, data, vars, mod)

    if constraints_df['Include']['meet_reserve_requirement'] == 1:
        mod = meet_reserve_requirement(sets, data, vars, mod)

    if constraints_df['Include']['power_lt_capacity'] == 1:
        mod = power_lt_capacity(sets, data, vars, mod)

    if constraints_df['Include']['intermittent_resource_availability'] == 1:
        mod = intermittent_resource_availability(sets, data, vars, mod)

    if constraints_df['Include']['commitment_continuity'] == 1:
        mod = commitment_continuity(sets, data, vars, mod)

    if constraints_df['Include']['max_units_committed'] == 1:
        mod = max_units_committed(sets, data, vars, mod)

    if constraints_df['Include']['power_lt_committed_capacity'] == 1:
        mod = power_lt_committed_capacity(sets, data, vars, mod)

    if constraints_df['Include']['power_gt_min_stable_gen'] == 1:
        mod = power_gt_min_stable_gen(sets, data, vars, mod)

    if constraints_df['Include']['minimum_up_time'] == 1:
        mod = minimum_up_time(sets, data, vars, mod, settings)

    if constraints_df['Include']['minimum_down_time'] == 1:
        mod = minimum_down_time(sets, data, vars, mod, settings)

    if constraints_df['Include']['energy_storage_continuity'] == 1:
        mod = energy_storage_continuity(sets, data, vars, mod, settings)

    if constraints_df['Include']['energy_storage_continuity_first_interval'] == 1:
        mod = energy_storage_continuity_first_interval(sets, data, vars, mod, settings)

    if constraints_df['Include']['max_stored_energy'] == 1:
        mod = max_stored_energy(sets, data, vars, mod)

    if constraints_df['Include']['max_charge'] == 1:
        mod = max_charge(sets, data, vars, mod)

    if constraints_df['Include']['maximum_reserve_enablement'] == 1:
        mod = maximum_reserve_enablement(sets, data, vars, mod)

    if constraints_df['Include']['limit_rocof'] == 1:
        mod = limit_rocof(sets, data, vars, mod, settings)

    if constraints_df['Include']['define_is_committed'] == 1:
        mod = define_is_committed(sets, data, vars, mod)

    return mod
