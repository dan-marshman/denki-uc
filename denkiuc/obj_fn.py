import pulp as pp


def physical_obj_fn_terms(sets, data, vars, settings):
    physical_obj_fn = \
        build_obj_vom_term(sets, data, vars, settings) \
        + build_obj_fuel_term(sets, data, vars, settings) \
        + build_obj_start_cost_term(sets, data, vars)
    return physical_obj_fn


def build_obj_vom_term(sets, data, vars, settings):
    obj_vom = \
        pp.lpSum([vars['power_generated_MW'][(i, u)]
                  * data.units['VOM_$pMWh'][u]
                  for i in sets.intervals for u in sets.units]) \
        / settings['INTERVALS_PER_HOUR']
    return obj_vom


def build_obj_fuel_term(sets, data, vars, settings):
    obj_fuel = \
        pp.lpSum([vars['power_generated_MW'][(i, u)]
                  * 3.6
                  * data.units['FuelCost_$pGJ'][u]
                  / data.units['ThermalEfficiency'][u]
                  for i in sets.intervals for u in sets.units_commit]) \
        / settings['INTERVALS_PER_HOUR']
    return obj_fuel


def build_obj_start_cost_term(sets, data, vars):
    obj_start_ups = \
        pp.lpSum([vars['start_up_status'][(i, u)]
                  * data.units['StartCost_$'][u]
                  for i in sets.intervals for u in sets.units_commit])
    return obj_start_ups


def unserved_obj_fn_terms(sets, data, vars, settings):
    obj_uns_demand = \
        pp.lpSum([settings['UNS_LOAD_PNTY']*vars['unserved_demand_MW'][i]
                  for i in sets.intervals]) \
        / settings['INTERVALS_PER_HOUR']

    obj_uns_reserve = \
        pp.lpSum([settings['UNS_RESERVE_PNTY']*vars['unserved_reserve_MW'][i]
                  for i in sets.intervals]) \
        / settings['INTERVALS_PER_HOUR']

    obj_uns_inertia = \
        pp.lpSum([settings['UNS_INERTIA_PNTY']*vars['unserved_inertia_MWsec'][i]
                  for i in sets.intervals]) \
        / settings['INTERVALS_PER_HOUR']
    
    unserved_terms = obj_uns_demand + obj_uns_reserve + obj_uns_inertia
    return unserved_terms


def obj_fn(sets, data, vars, settings):
    obj_fn = \
        physical_obj_fn_terms(sets, data, vars, settings) \
        + unserved_obj_fn_terms(sets, data, vars, settings)
    return obj_fn
