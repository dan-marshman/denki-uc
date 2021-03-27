import pulp as pp


def physical_obj_fn_terms(sets, data, vars, settings):
    physical_obj_fn = \
        build_obj_vom_term(sets, data, vars, settings) \
        + build_obj_fuel_term(sets, data, vars, settings) \
        + build_obj_start_cost_term(sets, data, vars)
    return physical_obj_fn


def build_obj_vom_term(sets, data, vars, settings):
    obj_vom = \
        pp.lpSum(
                 [vars['power_generated'].var[(i, s, u)] * data.units['VOM_$pMWh'][u]
                  * data.probability_of_scenario[s]
                  for i in sets['intervals'].indices
                  for u in sets['units'].indices for s in sets['scenarios'].indices]
                )
    obj_vom /= settings['INTERVALS_PER_HOUR']

    return obj_vom


def build_obj_fuel_term(sets, data, vars, settings):
    obj_fuel = \
        pp.lpSum(
                 [vars['power_generated'].var[(i, s, u)]
                  * 3.6 * data.units['FuelCost_$pGJ'][u] / data.units['ThermalEfficiency'][u]
                  * data.probability_of_scenario[s]
                  for i in sets['intervals'].indices
                  for u in sets['units_commit'].indices for s in sets['scenarios'].indices]
                )
    obj_fuel /= settings['INTERVALS_PER_HOUR']

    return obj_fuel


def build_obj_start_cost_term(sets, data, vars):
    obj_start_ups = \
        pp.lpSum(
                 [vars['num_starting_up'].var[(i, s, u)] * data.units['StartCost_$'][u]
                  for i in sets['intervals'].indices
                  for s in sets['scenarios'].indices
                  for u in sets['units_commit'].indices]
                )

    return obj_start_ups


def unserved_obj_fn_terms(sets, data, vars, settings):
    obj_uns_power = \
        pp.lpSum(
                 [settings['UNS_LOAD_PNTY'] * vars['unserved_power'].var[(i, s)]
                  * data.probability_of_scenario[s]
                  for i in sets['intervals'].indices for s in sets['scenarios'].indices]
                )

    obj_uns_reserve = \
        pp.lpSum(
                 [settings['UNS_RESERVE_PNTY'] * vars['unserved_reserve'].var[(i, s, r)]
                  * data.probability_of_scenario[s]
                  for i in sets['intervals'].indices
                  for s in sets['scenarios'].indices
                  for r in sets['reserves'].indices]
                )

    obj_uns_inertia = \
        pp.lpSum(
                 [settings['UNS_INERTIA_PNTY'] * vars['unserved_inertia'].var[i]
                  for i in sets['intervals'].indices]
                )

    unserved_terms = \
        (obj_uns_power + obj_uns_reserve + obj_uns_inertia) / settings['INTERVALS_PER_HOUR']

    return unserved_terms


def obj_fn(sets, data, vars, settings):
    obj_fn = \
        physical_obj_fn_terms(sets, data, vars, settings) \
        + unserved_obj_fn_terms(sets, data, vars, settings)
    return obj_fn
