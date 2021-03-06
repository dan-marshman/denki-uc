import pulp as pp


def supply_eq_demand(sets, data, vars, mod):
    for i in sets.intervals:

        label = 'meet_demand_i_%d' % i
        
        condition = \
            (
             pp.lpSum([vars['power_generated_MW'][(i, u)]
                      for u in sets.units])
             + vars['unserved_demand_MW'][i]
             ==
             data.traces['demand']['VIC'][i]
             + pp.lpSum([vars['charge_after_losses_MW'][(i, u)]
                         * (1 / data.units['RTEfficiency'][u])
                        for u in sets.units_storage])
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
    
    for u in sets.units_variable:
        region = data.units['Region'][u]
        technology = data.units['Technology'][u]
        trace = get_resource_trace(region, technology)

        for i in sets.intervals:
            label = 'variable_resource_availability_u_%s_i_%s' % (u, i)
            
            condition = \
                (
                 vars['power_generated_MW'][(i, u)] \
                     <= trace[i] * data.units['Capacity_MW'][u]
                )

            mod += condition, label

    return mod


def power_lt_committed_capacity(sets, data, vars, mod):
    for i in sets.intervals:
        for u in sets.units:
            label = 'power_lt_cap_%s_int_%s' % (u, i)

            condition = \
                (vars['power_generated_MW'][(i, u)] + vars['reserve_MW'][(i, u)]
                 <=
                 vars['commit_status'][(i, u)] * data.units['Capacity_MW'][u])

            mod += condition, label
    return mod


def power_lt_capacity(sets, data, vars, mod):
    for i in sets.intervals:
        for u in sets.units:
            label = 'power_lt_cap_%s_int_%s' % (u, i)
            
            condition = \
                (vars['power_generated_MW'][(i, u)] + vars['reserve_MW'][(i, u)]
                 <=
                 data.units['Capacity_MW'][u]
                )
            
            mod += condition, label
    return mod


def energy_storage_continuity(sets, data, vars, mod, settings):
    for i in sets.intervals:
        if i > min(sets.intervals):
            for u in sets.units_storage:
                label = 'storage_continuity_%s_int_%s' % (u, i)

                condition = \
                    (vars['energy_in_storage_MWh'][(i, u)]
                     ==
                     vars['energy_in_storage_MWh'][(i-1, u)]
                     + vars['charge_after_losses_MW'][(i, u)] * (1 / settings['INTERVALS_PER_HOUR'])
                     - vars['power_generated_MW'][(i, u)] * (1 / settings['INTERVALS_PER_HOUR'])
                    )
                mod += condition, label
    return mod


def energy_storage_continuity_first_interval(sets, data, vars, mod, settings):
    for u in sets.units_storage:
        i = min(sets.intervals)
        initial_energy_in_storage_MWh \
            = (data.initial_state['StorageLevel_frac'][u]
               * data.units['StorageCap_h'][u]
               * data.units['Capacity_MW'][u])
        label = 'storage_continuity_%s_int_%s' % (u, i)
        condition = \
            (vars['energy_in_storage_MWh'][(i, u)]
             ==
             initial_energy_in_storage_MWh
             + vars['charge_after_losses_MW'][(i, u)] * (1 / settings['INTERVALS_PER_HOUR'])
             - vars['power_generated_MW'][(i, u)] * (1 / settings['INTERVALS_PER_HOUR']))
        mod += condition, label
    return mod


def max_stored_energy(sets, data, vars, mod):
    for i in sets.intervals:
        for u in sets.units_storage:
            label = 'max_stored_energy_%s_int_%s' % (u, i)
            
            condition = \
                (
                 vars['energy_in_storage_MWh'][(i, u)]
                 <=
                 data.units['StorageCap_h'][u] * data.units['Capacity_MW'][u]
                )

            mod += condition, label
    return mod


def max_charge(sets, data, vars, mod):
    for i in sets.intervals:
        for u in sets.units_storage:
            label = 'max_charge_%s_int_%s' % (u, i)
            condition = \
                (vars['charge_after_losses_MW'][(i, u)]
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
    
    if constraints_df['Include']['energy_storage_continuity'] == 1:
        mod = energy_storage_continuity(sets, data, vars, mod, settings)
    
    if constraints_df['Include']['energy_storage_continuity_first_interval'] == 1:
        mod = energy_storage_continuity_first_interval(sets, data, vars, mod, settings)
    
    if constraints_df['Include']['max_stored_energy'] == 1:
        mod = max_stored_energy(sets, data, vars, mod)

    if constraints_df['Include']['max_charge'] == 1:
        mod = max_charge(sets, data, vars, mod)

    return mod
