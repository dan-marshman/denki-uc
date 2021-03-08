import pulp as pp


def supply_eq_demand(sets, data, vars, mod):
    
    for i in sets['intervals'].indices:

        label = 'meet_demand_i_%d' % i
        
        condition = \
            (
             pp.lpSum([vars['power_generated'].var[(i, u)]
                      for u in sets['units'].indices])
             + vars['unserved_power'].var[i]
             ==
             data.traces['demand']['VIC'][i]
             + pp.lpSum([vars['charge_after_losses'].var[(i, u)]
                         * (1 / data.units['RTEfficiency'][u])
                        for u in sets['units_storage'].indices])
             )
        
        mod += condition, label
    return mod


def intermittent_resource_availability(sets, data, vars, mod):

    def get_resource_trace(region, technology):
        if technology == 'Wind':
            trace = data.traces['wind']['VIC'].to_dict()
        elif technology == 'SolarPV':
            trace = data.traces['solarPV']['VIC'].to_dict()
        else:
            print('Technology not known')
            exit()
        return trace
    
    for u in sets['units_variable'].indices:
        region = data.units['Region'][u]
        technology = data.units['Technology'][u]
        trace = get_resource_trace(region, technology)

        for i in sets['intervals'].indices:
            label = 'variable_resource_availability_u_%s_i_%s' % (u, i)
            
            condition = \
                (
                 vars['power_generated'].var[(i, u)] \
                     <= trace[i] * data.units['Capacity_MW'][u]
                )

            mod += condition, label

    return mod


def commitment_continuity(sets, data, vars, mod):
    for i in sets['intervals'].indices:

        for u in sets['units_commit'].indices:
            if i == min(sets['intervals'].indices):
                label = 'commitment_continuity_%s_int_%s' % (u, i)

                condition = \
                    (
                     vars['commit_status'].var[(i, u)] 
                     == 
                     data.initial_state['Commit'][u]
                     + vars['start_up_status'].var[(i, u)]
                     - vars['shut_down_status'].var[(i, u)]
                     )

            if i > min(sets['intervals'].indices):
                label = 'commitment_continuity_%s_int_%s' % (u, i)

                condition = \
                    (
                     vars['commit_status'].var[(i, u)] 
                     == 
                     vars['commit_status'].var[(i-1, u)]
                     + vars['start_up_status'].var[(i, u)]
                     - vars['shut_down_status'].var[(i, u)]
                     )

            mod += condition, label

    return mod


def power_lt_committed_capacity(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for u in sets['units_commit'].indices:
            label = 'power_lt_commited_cap_%s_int_%s' % (u, i)

            condition = \
                (vars['power_generated'].var[(i, u)] + vars['reserve_enablement'].var[(i, u)]
                 <=
                 vars['commit_status'].var[(i, u)] * data.units['Capacity_MW'][u])

            mod += condition, label
    return mod


def power_gt_min_stable_gen(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for u in sets['units_commit'].indices:
            label = 'power_gt_min_stable_gen_%s_int_%s' % (u, i)

            condition = \
                (vars['power_generated'].var[(i, u)]
                 >=
                 vars['commit_status'].var[(i, u)] * data.units['Capacity_MW'][u] * data.units['MinGen'][u])

            mod += condition, label
    return mod


def power_lt_capacity(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for u in sets['units'].indices:
            label = 'power_lt_cap_%s_int_%s' % (u, i)
            
            condition = \
                (vars['power_generated'].var[(i, u)] + vars['reserve_enablement'].var[(i, u)]
                 <=
                 data.units['Capacity_MW'][u]
                )
            
            mod += condition, label
    return mod


def energy_storage_continuity(sets, data, vars, mod, settings):
    for i in sets['intervals'].indices:
        if i > min(sets['intervals'].indices):
            for u in sets['units_storage'].indices:
                label = 'storage_continuity_%s_int_%s' % (u, i)

                condition = \
                    (vars['energy_in_reservoir'].var[(i, u)]
                     ==
                     vars['energy_in_reservoir'].var[(i-1, u)]
                     + vars['charge_after_losses'].var[(i, u)] * (1 / settings['INTERVALS_PER_HOUR'])
                     - vars['power_generated'].var[(i, u)] * (1 / settings['INTERVALS_PER_HOUR'])
                    )
                mod += condition, label
    return mod


def energy_storage_continuity_first_interval(sets, data, vars, mod, settings):
    for u in sets['units_storage'].indices:
        i = min(sets['intervals'].indices)
        initial_energy_in_reservoir \
            = (data.initial_state['StorageLevel_frac'][u]
               * data.units['StorageCap_h'][u]
               * data.units['Capacity_MW'][u])
        label = 'storage_continuity_%s_int_%s' % (u, i)
        condition = \
            (vars['energy_in_reservoir'].var[(i, u)]
             ==
             initial_energy_in_reservoir
             + vars['charge_after_losses'].var[(i, u)] * (1 / settings['INTERVALS_PER_HOUR'])
             - vars['power_generated'].var[(i, u)] * (1 / settings['INTERVALS_PER_HOUR']))
        mod += condition, label
    return mod


def max_stored_energy(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for u in sets['units_storage'].indices:
            label = 'max_stored_energy_%s_int_%s' % (u, i)
            
            condition = \
                (
                 vars['energy_in_reservoir'].var[(i, u)]
                 <=
                 data.units['StorageCap_h'][u] * data.units['Capacity_MW'][u]
                )

            mod += condition, label
    return mod


def max_charge(sets, data, vars, mod):
    for i in sets['intervals'].indices:
        for u in sets['units_storage'].indices:
            label = 'max_charge_%s_int_%s' % (u, i)
            condition = \
                (vars['charge_after_losses'].var[(i, u)]
                 <=
                 data.units['RTEfficiency'][u]
                 * data.units['Capacity_MW'][u])
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

    if constraints_df['Include']['power_lt_capacity'] == 1:
        mod = power_lt_capacity(sets, data, vars, mod)

    if constraints_df['Include']['intermittent_resource_availability'] == 1:
        mod = intermittent_resource_availability(sets, data, vars, mod)
    
    if constraints_df['Include']['commitment_continuity'] == 1:
        mod = commitment_continuity(sets, data, vars, mod)
    
    if constraints_df['Include']['power_lt_committed_capacity'] == 1:
        mod = power_lt_committed_capacity(sets, data, vars, mod)
    
    if constraints_df['Include']['power_gt_min_stable_gen'] == 1:
        mod = power_gt_min_stable_gen(sets, data, vars, mod)
    
    if constraints_df['Include']['energy_storage_continuity'] == 1:
        mod = energy_storage_continuity(sets, data, vars, mod, settings)
    
    if constraints_df['Include']['energy_storage_continuity_first_interval'] == 1:
        mod = energy_storage_continuity_first_interval(sets, data, vars, mod, settings)
    
    if constraints_df['Include']['max_stored_energy'] == 1:
        mod = max_stored_energy(sets, data, vars, mod)

    if constraints_df['Include']['max_charge'] == 1:
        mod = max_charge(sets, data, vars, mod)

    return mod
