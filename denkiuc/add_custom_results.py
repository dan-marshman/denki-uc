import os
import pandas as pd


def add_custom_results(data, results, results_path, settings, sets):
    new_results = dict()

    new_results['charge_losses'] = add_charge_losses(data, results)
    new_results['total_charge_load'] = add_total_charge_load(results, new_results)
    new_results['dispatch'] = add_dispatch_result(data, results, new_results)
    new_results['final_state'] = add_final_state(data, results, sets)
    new_results = add_traces_to_new_results(data, new_results)

    if settings['INCL_UNIT_COMMITMENT']:
        new_results['inertia_dispatch'] = add_inertia_dispatch(data, results)
        new_results['max_rocof'] = add_maximum_rocof(data, new_results, settings)

    for name, result in new_results.items():
        # result = result.round(3)
        filename = name + '.csv'
        write_path = os.path.join(results_path, filename)
        result.to_csv(write_path)

    results.update(new_results)

    return results


def add_charge_losses(data, results):
    charge_losses = results['charge_after_losses'].copy()

    for col in charge_losses.columns.to_list():
        u = col[1]
        rt_eff = data['units']['RTEfficiency'][u]
        charge_losses[col] = charge_losses[col] * (1 - rt_eff) / rt_eff

    return charge_losses


def add_total_charge_load(results, new_results):
    total_charge_load = results['charge_after_losses'].add(new_results['charge_losses'])
    return total_charge_load


def add_inertia_dispatch(data, results):
    inertia_dispatch = results['num_commited'].copy()

    for col in inertia_dispatch.columns:
        for i in inertia_dispatch.index:
            u = col[1]
            inertia_dispatch.loc[i, col] = \
                inertia_dispatch.loc[i, col] \
                * data['units']['InertialConst_s'][u] * data['units']['Capacity_MW'][u]

    scenarios = set([c[0] for c in inertia_dispatch.columns])
    for s in scenarios:
        filtered_cols = [c for c in inertia_dispatch.columns if c[0] == s]
        inertia_dispatch[(s, 'SystemInertia')] = inertia_dispatch[filtered_cols].sum(axis=1)

    return inertia_dispatch


def add_maximum_rocof(data, new_results, settings):
    df_cols = ['MaxRocof', 'RocofLimit', 'ResponsibleUnit']
    df_index = new_results['inertia_dispatch'].index
    max_rocof_df = pd.DataFrame(index=df_index, columns=df_cols)

    max_rocof_df.loc[:, 'RocofLimit'] = settings['MAX_ROCOF']

    df_cols = new_results['inertia_dispatch'].columns
    units = set([c[1] for c in df_cols if c[1] != 'SystemInertia'])
    scenarios = set([c[0] for c in df_cols if c[1] != 'SystemInertia'])

    for i in new_results['inertia_dispatch'].index:
        max_rocof = 0
        for s in scenarios:
            system_inertia = new_results['inertia_dispatch'][(s, 'SystemInertia')][i]
            for u in units:
                units_inertia = new_results['inertia_dispatch'][(s, u)][i]
                available_inertia = system_inertia - units_inertia
                contingency_size = \
                    new_results['inertia_dispatch'][(s, u)][i] \
                    / data['units']['InertialConst_s'][u]

                rocof_in_units_failure = \
                    contingency_size * settings['SYSTEM_FREQUENCY'] / (2 * available_inertia)

                if rocof_in_units_failure > max_rocof:
                    max_rocof = rocof_in_units_failure
                    responsible_unit = u

            max_rocof_df.loc[i, 'MaxRocof'] = max_rocof
            max_rocof_df.loc[i, 'ResponsibleUnit'] = responsible_unit

    return max_rocof_df


def add_dispatch_result(data, results, new_results):
    def add_level_and_join(dispatch, new_df, category):
        new_df = pd.concat([new_df], axis=1, keys=[category])
        new_df = new_df.swaplevel(0, 2, axis=1).swaplevel(0, 1, axis=1)
        dispatch = dispatch.join(new_df)

        return dispatch

    dispatch = results['power_generated'].copy()
    dispatch = pd.concat([dispatch], axis=1, keys=['generation'])
    dispatch = dispatch.swaplevel(0, 2, axis=1).swaplevel(0, 1, axis=1)

    dispatch = add_level_and_join(dispatch, -1 * results['charge_after_losses'], 'charge')
    dispatch = add_level_and_join(dispatch, -1 * new_results['charge_losses'], 'losses')
    dispatch = add_level_and_join(dispatch, -1 * data['traces']['demand'], 'demand')

    unserved_df = results['unserved_power'].copy()
    unserved_df.columns = pd.MultiIndex.from_product([unserved_df.columns, ['Demand']])
    dispatch = add_level_and_join(dispatch, unserved_df, 'unserved')

    return dispatch


def add_final_state(data, vars, sets, paths):
    final_state = dict()
    final_interval = max(sets['main_intervals'].indices)
    first_scenario = min(sets['scenarios'].indices)

    final_state['power_generated'] = pd.Series(index=sets['units'].indices)
    for u in sets['units'].indices:
        final_state['power_generated'].loc[u] = \
            vars['power_generated'].result_df[(first_scenario, u)][final_interval]

    final_state['storage_fraction'] = pd.Series(index=sets['units_storage'].indices)
    for u in sets['units_storage'].indices:
        final_state['storage_fraction'].loc[u] = \
            vars['energy_in_reservoir'].result_df[(first_scenario, u)][final_interval] \
            / (data['units']['Capacity_MW'][u] * data['units']['StorageCap_h'][u])
    return final_state


def add_traces_to_new_results(data, new_results):
    for trace_name, trace in data['traces'].items():
        new_results[trace_name] = trace

    return new_results
