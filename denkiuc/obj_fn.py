import pulp as pp
import denkiuc.misc_functions as mf


def build_obj_capital_term(prob):
    sets, data, vars, settings = mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'settings'])

    obj_capital_cost = \
        pp.lpSum(
                 [vars['num_built'].var[u] * data['units']['CapitalCost_$pMW'][u]
                  * data['units']['Capacity_MW'][u]
                  for u in sets['units'].indices]
                )

    obj_capital_cost /= (8760 * len(sets['intervals'].indices) / settings['INTERVALS_PER_HOUR'])

    return obj_capital_cost


def build_obj_vom_term(prob):
    sets, data, vars, settings = mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'settings'])

    obj_vom_cost = \
        pp.lpSum(
                 [vars['power_generated'].var[(i, s, u)] * data['units']['VOM_$pMWh'][u]
                  * data['probability_of_scenario'][s]
                  for i in sets['intervals'].indices
                  for u in sets['units'].indices
                  for s in sets['scenarios'].indices]
                )

    obj_vom_cost /= settings['INTERVALS_PER_HOUR']

    return obj_vom_cost


def build_obj_fuel_term(prob):
    sets, data, vars, settings = mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'settings'])

    obj_fuel_cost = \
        pp.lpSum(
                 [vars['power_generated'].var[(i, s, u)]
                  * 3.6 * data['units']['FuelCost_$pGJ'][u] / data['units']['ThermalEfficiency'][u]
                  * data['probability_of_scenario'][s]
                  for i in sets['intervals'].indices
                  for u in sets['units_commit'].indices
                  for s in sets['scenarios'].indices]
                )

    obj_fuel_cost /= settings['INTERVALS_PER_HOUR']

    return obj_fuel_cost


def build_obj_start_cost_term(prob):
    sets, data, vars, = mf.prob_unpacker(prob, ['sets', 'data', 'vars'])

    obj_start_up_cost = \
        pp.lpSum(
                 [vars['num_starting_up'].var[(i, s, u)] * data['units']['StartCost_$'][u]
                  for i in sets['intervals'].indices
                  for s in sets['scenarios'].indices
                  for u in sets['units_commit'].indices]
                )

    return obj_start_up_cost


def build_obj_rec_value_term(prob):
    sets, data, vars, settings = mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'settings'])

    obj_rec_value = \
        pp.lpSum(
                 [vars['power_generated'].var[(i, s, u)] * settings['REC_PRICE']
                  * data['probability_of_scenario'][s]
                  for i in sets['intervals'].indices
                  for u in sets['units_renewable'].indices
                  for s in sets['scenarios'].indices]
                )

    obj_rec_value /= settings['INTERVALS_PER_HOUR']

    return obj_rec_value


def build_obj_carbon_price_term(prob):
    sets, data, vars, settings = mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'settings'])

    obj_rec_value = \
        pp.lpSum(
                 [vars['power_generated'].var[(i, s, u)]
                  * settings['CARBON_PRICE']
                  * data['probability_of_scenario'][s]
                  * 3.6 * data['units']['Emissions_tonneCO2epGJ'][u]
                  / data['units']['ThermalEfficiency'][u]
                  for i in sets['intervals'].indices
                  for u in sets['units_thermal'].indices
                  for s in sets['scenarios'].indices]
                )

    obj_rec_value /= settings['INTERVALS_PER_HOUR']

    return obj_rec_value


def unserved_obj_fn_terms(prob):
    sets, data, vars, settings = mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'settings'])

    obj_uns_power = \
        pp.lpSum(
                 [settings['UNS_LOAD_PNTY'] * vars['unserved_power'].var[(i, s)]
                  * data['probability_of_scenario'][s]
                  for i in sets['intervals'].indices for s in sets['scenarios'].indices]
                )

    obj_uns_reserve = \
        pp.lpSum(
                 [settings['UNS_RESERVE_PNTY'] * vars['unserved_reserve'].var[(i, s, r)]
                  * data['probability_of_scenario'][s]
                  for i in sets['intervals'].indices
                  for s in sets['scenarios'].indices
                  for r in sets['reserves'].indices]
                )

    obj_uns_inertia = \
        pp.lpSum(
                 [settings['UNS_INERTIA_PNTY'] * vars['unserved_inertia'].var[i]
                  for i in sets['intervals'].indices]
                )

    obj_unserved_penalties = \
        (obj_uns_power + obj_uns_reserve + obj_uns_inertia) / settings['INTERVALS_PER_HOUR']

    return obj_unserved_penalties


def obj_fn(prob):
    obj_capital_cost = build_obj_capital_term(prob)

    obj_vom_cost = build_obj_vom_term(prob)
    obj_fuel_cost = build_obj_fuel_term(prob)
    obj_start_up_cost = build_obj_start_cost_term(prob)

    obj_unserved_penalties = unserved_obj_fn_terms(prob)

    obj_rec_value = build_obj_rec_value_term(prob)
    obj_carbon_cost = build_obj_carbon_price_term(prob)

    obj_fn = \
        obj_capital_cost \
        + (obj_vom_cost + obj_fuel_cost + obj_start_up_cost) \
        + obj_unserved_penalties \
        + obj_carbon_cost \
        - obj_rec_value

    return obj_fn
