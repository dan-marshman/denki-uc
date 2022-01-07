import pulp as pp


def cnt_supply_eq_demand(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            label = 'meet_demand_i_%d_s_%d' % (i, s)

            condition = \
                (
                 pp.lpSum([vars['power_generated'].var[(i, s, u)]
                           for u in sets['units'].indices])
                 + vars['unserved_power'].var[(i, s)]
                 ==
                 data.traces['demand'][s][i]
                 + pp.lpSum([vars['charge_after_losses'].var[(i, s, u)]
                             * (1 / data.units['RTEfficiency'][u])
                             for u in sets['units_storage'].indices])
                 )

            mod += condition, label
    return mod


def cnt_meet_reserve_requirement(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

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


def cnt_variable_resource_availability(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

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


def cnt_commitment_continuity(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for u in sets['units_commit'].indices:

            if i == min(sets['intervals'].indices):
                for s in sets['scenarios'].indices:
                    label = 'commitment_continuity_%s_i_%s_s_%d' % (u, i, s)

                    condition = \
                        (
                         vars['num_committed'].var[(i, s, u)]
                         ==
                         data.initial_state['NumCommited'][u]
                         + vars['num_starting_up'].var[(i, s, u)]
                         - vars['num_shutting_down'].var[(i, s, u)]
                         )

                    mod += condition, label

            if i > min(sets['intervals'].indices):
                label = 'commitment_continuity_%s_i_%s_s+%d' % (u, i, s)

                condition = \
                    (
                     vars['num_committed'].var[(i, s, u)]
                     ==
                     vars['num_committed'].var[(i-1, s, u)]
                     + vars['num_starting_up'].var[(i, s, u)]
                     - vars['num_shutting_down'].var[(i, s, u)]
                     )

                mod += condition, label

    return mod


def cnt_inflexible_commitment(attr):
    sets = attr['sets']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_inflex'].indices:
                label = 'inflexible_commit_same_across_scenarios_u_%s_i_%s_s_%s' % (u, s, i)
                condition = \
                    (
                     vars['num_committed'].var[(i, s, u)]
                     ==
                     vars['num_committed_all_scenarios'].var[(i, u)]
                     )

            mod += condition, label

    return mod


def cnt_max_units_committed(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'num_units_commit_lt_exist_%s_int_%s_s_%d' % (u, i, s)

                condition = \
                    (vars['num_committed'].var[(i, s, u)]
                     <=
                     data.units['NoUnits'][u])

                mod += condition, label

    return mod


def cnt_power_lt_committed_capacity(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'power_lt_commited_cap_%s_int_%s_s_%s' % (u, i, s)

                condition = \
                    (vars['power_generated'].var[(i, s, u)]
                     + pp.lpSum(vars['reserve_enabled'].var[(i, s, u, r)]
                                for r in sets['raise_reserves'].indices)
                     <=
                     vars['num_committed'].var[(i, s, u)] * data.units['Capacity_MW'][u])

                mod += condition, label

    return mod


def cnt_power_gt_min_stable_gen(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'power_gt_min_stable_gen_%s_int_%s_s_%s' % (u, i, s)

                condition = \
                    (vars['power_generated'].var[(i, s, u)]
                     - pp.lpSum(vars['reserve_enabled'].var[(i, s, u, r)]
                                for r in sets['lower_reserves'].indices)
                     >=
                     vars['num_committed'].var[(i, s, u)]
                     * data.units['Capacity_MW'][u]
                     * data.units['MinGen_pctCap'][u])

                mod += condition, label
    return mod


def cnt_power_lt_capacity(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

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


def cnt_minimum_up_time(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

    i0 = min(sets['intervals'].indices)

    for i in sets['intervals'].indices:
        i_high = i + 1

        for u in sets['units_commit'].indices:
            unit_up_time = data.units['MinUpTime_h'][u]
            i_low = 1 + max(i0 - 1, i - settings['INTERVALS_PER_HOUR'] * unit_up_time)

            for s in sets['scenarios'].indices:
                label = 'minimum_up_time_i_%d_u_%s_s_%d' % (i, u, s)

                condition = (
                    vars['num_committed'].var[(i, s, u)]
                    >=
                    pp.lpSum([vars['num_starting_up'].var[(i2, s, u)]
                              for i2 in range(i_low, i_high)])
                    )

                mod += condition, label

    return mod


def cnt_minimum_down_time(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

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
                    data.units['NoUnits'][u] - vars['num_committed'].var[(i, s, u)]
                    >=
                    pp.lpSum([vars['num_shutting_down'].var[(i2, s, u)]
                              for i2 in range(i_low, i_high)])
                    )

                mod += condition, label

    return mod


def cnt_storage_continuity(attr):
    sets = attr['sets']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

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


def cnt_storage_continuity_first_int(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

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


def cnt_max_stored_energy(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

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


def cnt_max_charge(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

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


def cnt_maximum_reserve_enablement(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

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
                            vars['num_committed'].var[(i, s, u)] * max_reserves_per_unit
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


def cnt_limit_rocof(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

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
                pp.lpSum(vars['num_committed'].var[(i, s, u2)]
                         * data.units['InertialConst_s'][u2]
                         * data.units['Capacity_MW'][u2]
                         for u2 in sets['units_commit'].indices)

            for u in sets['units'].indices:
                label = 'limit_rocof_%s_int_%d_s_%d' % (u, i, s)

                if u in sets['units_commit'].indices:
                    units_inertia = \
                        vars['num_committed'].var[(i, s, u)] \
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


def cnt_define_is_committed(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'define_is_committed_%s_int_%d_s_%d' % (u, i, s)

                condition = \
                    (
                     vars['num_committed'].var[(i, s, u)]
                     <=
                     vars['is_committed'].var[(i, s, u)] * data.units['NoUnits'][u]
                    )

                mod += condition, label

    return mod


def cnt_ramp_rate_up(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'ramp_rate_up_%s_int_%d_s_%d' % (u, i, s)

                if i == sets['intervals'].indices[0]:
                    ramp = \
                        vars['power_generated'].var[(i, s, u)] \
                        - data.initial_state['PowerGeneration_MW'][u]
                else:
                    ramp = \
                        vars['power_generated'].var[(i, s, u)] \
                        - vars['power_generated'].var[(i-1, s, u)]

                committed_ramp_capacity = \
                    vars['num_committed'].var[(i, s, u)] \
                    * data.units['RampRateUp_pctCapphr'][u] \
                    * data.units['Capacity_MW'][u] \
                    / settings['INTERVALS_PER_HOUR']

                start_up_ramp_capacity = \
                    vars['num_starting_up'].var[(i, s, u)] \
                    * max(data.units['RampRateUp_pctCapphr'][u] / settings['INTERVALS_PER_HOUR'],
                          data.units['MinGen_pctCap'][u]) \
                    * data.units['Capacity_MW'][u]

                condition = ramp <= committed_ramp_capacity + start_up_ramp_capacity

                mod += condition, label

    return mod


def cnt_ramp_rate_down(attr):
    sets = attr['sets']
    data = attr['data']
    vars = attr['vars']
    mod = attr['mod']
    settings = attr['settings']

    for i in sets['intervals'].indices:
        for s in sets['scenarios'].indices:
            for u in sets['units_commit'].indices:
                label = 'ramp_rate_down_%s_int_%d_s_%d' % (u, i, s)

                if i == sets['intervals'].indices[0]:
                    ramp = \
                        data.initial_state['PowerGeneration_MW'][u] \
                        - vars['power_generated'].var[(i, s, u)]
                else:
                    ramp = \
                        vars['power_generated'].var[(i-1, s, u)] \
                        - vars['power_generated'].var[(i, s, u)]

                committed_ramp_capacity = \
                    vars['num_committed'].var[(i, s, u)] \
                    * data.units['RampRateUp_pctCapphr'][u] \
                    * data.units['Capacity_MW'][u] \
                    / settings['INTERVALS_PER_HOUR']

                shut_down_ramp_capacity = \
                    vars['num_shutting_down'].var[(i, s, u)] \
                    * max(data.units['RampRateDown_pctCapphr'][u] / settings['INTERVALS_PER_HOUR'],
                          data.units['MinGen_pctCap'][u]) \
                    * data.units['Capacity_MW'][u]

                condition = ramp <= committed_ramp_capacity + shut_down_ramp_capacity

                mod += condition, label

    return mod


def create_cnts_df(path_to_inputs):
    import os
    import pandas as pd

    cnts_df = pd.read_csv(os.path.join(path_to_inputs, 'constraints.csv'), index_col=0)
    cnts_df['Cnst'] = ''

    return cnts_df


def add_basic_constraints(attr):
    attr['mod'] = cnt_supply_eq_demand(attr)
    attr['mod'] = cnt_meet_reserve_requirement(attr)
    attr['mod'] = cnt_power_lt_capacity(attr)
    attr['mod'] = cnt_variable_resource_availability(attr)
    attr['mod'] = cnt_maximum_reserve_enablement(attr)

    return attr


def add_uc_constraints(attr):
    attr['mod'] = cnt_commitment_continuity(attr)
    attr['mod'] = cnt_max_units_committed(attr)
    attr['mod'] = cnt_power_lt_committed_capacity(attr)
    attr['mod'] = cnt_power_gt_min_stable_gen(attr)
    attr['mod'] = cnt_minimum_up_time(attr)
    attr['mod'] = cnt_minimum_down_time(attr)
    attr['mod'] = cnt_limit_rocof(attr)
    attr['mod'] = cnt_define_is_committed(attr)
    attr['mod'] = cnt_ramp_rate_up(attr)
    attr['mod'] = cnt_ramp_rate_down(attr)

    return attr


def add_storage_constraints(attr):
    attr['mod'] = cnt_storage_continuity(attr)
    attr['mod'] = cnt_storage_continuity_first_int(attr)
    attr['mod'] = cnt_max_stored_energy(attr)
    attr['mod'] = cnt_max_charge(attr)

    return attr


def add_constraints_to_model(attr):
    attr = add_basic_constraints(attr)
    attr = add_storage_constraints(attr)

    if attr['settings']['INCL_UNIT_COMMITMENT']:
        attr = add_uc_constraints(attr)

    return attr


def add_all_constraints_to_dataframe(sets, data, vars, settings, mod, cnts_df):
    attr = {'sets': sets, 'data': data, 'vars': vars, 'mod': mod, 'settings': settings}

    cnts_df.loc['supply_eq_demand', 'Cnst'] = cnt_supply_eq_demand
    cnts_df.loc['meet_reserve_requirement', 'Cnst'] = cnt_meet_reserve_requirement
    cnts_df.loc['power_lt_capacity', 'Cnst'] = cnt_power_lt_capacity
    cnts_df.loc['variable_resource_availability', 'Cnst'] = cnt_variable_resource_availability
    cnts_df.loc['commitment_continuity', 'Cnst'] = cnt_commitment_continuity
    cnts_df.loc['max_units_committed', 'Cnst'] = cnt_max_units_committed
    cnts_df.loc['power_lt_committed_capacity', 'Cnst'] = cnt_power_lt_committed_capacity
    cnts_df.loc['power_gt_min_stable_gen', 'Cnst'] = cnt_power_gt_min_stable_gen
    cnts_df.loc['minimum_up_time', 'Cnst'] = cnt_minimum_up_time
    cnts_df.loc['minimum_down_time', 'Cnst'] = cnt_minimum_down_time
    cnts_df.loc['ramp_rate_up', 'Cnst'] = cnt_ramp_rate_up
    cnts_df.loc['ramp_rate_down', 'Cnst'] = cnt_ramp_rate_down
    cnts_df.loc['storage_continuity', 'Cnst'] = cnt_storage_continuity
    cnts_df.loc['storage_continuity_first_int', 'Cnst'] = cnt_storage_continuity_first_int
    cnts_df.loc['max_stored_energy', 'Cnst'] = cnt_max_stored_energy
    cnts_df.loc['max_charge', 'Cnst'] = cnt_max_charge
    cnts_df.loc['maximum_reserve_enablement', 'Cnst'] = cnt_maximum_reserve_enablement
    cnts_df.loc['limit_rocof', 'Cnst'] = cnt_limit_rocof
    cnts_df.loc['define_is_committed', 'Cnst'] = cnt_define_is_committed

    cnts_to_add_df = cnts_df[cnts_df['Include'] == 1]
    for cnt in cnts_to_add_df.index:
        attr['mod'] = cnts_df['Cnst'][cnt](attr)

    return mod
