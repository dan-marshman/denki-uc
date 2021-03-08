import os
import pandas as pd


def add_custom_results(data, results, results_path):
    new_results = dict()
    
    new_results['charge_losses'] = add_charge_losses(data, results)
    new_results['total_charge_load'] = add_total_charge_load(results, new_results)
    new_results['dispatch'] = add_dispatch_result(data, results, new_results)

    for name, result in new_results.items():
        result = result.round(3)
        filename = name + '.csv'
        write_path = os.path.join(results_path, filename)
        result.to_csv(write_path)

    results.update(new_results)

    return results


def add_charge_losses(data, results):
    charge_losses = results['charge_after_losses'].copy()
    for col in charge_losses.columns.to_list():
        charge_losses[col] = charge_losses[col] / (data.units['RTEfficiency'][col]) * (1 - data.units['RTEfficiency'][col])
    return charge_losses


def add_total_charge_load(results, new_results):
    total_charge_load = results['charge_after_losses'].add(new_results['charge_losses'])
    return total_charge_load


def add_dispatch_result(data, results, new_results):
    dispatch = results['power_generated'].copy()

    demand_df = -1 * data.traces['demand'].copy()
    demand_df = demand_df.rename(columns={r: r+' demand' for r in demand_df.columns.to_list()})
    dispatch = dispatch.join(demand_df)

    charge_df = -1 * results['charge_after_losses'].copy()
    charge_df = charge_df.rename(columns={r: r+' charge after losses' for r in charge_df.columns.to_list()})
    dispatch = dispatch.join(charge_df)

    charge_losses_df = -1 * new_results['charge_losses'].copy()
    charge_losses_df = charge_losses_df.rename(columns={r: r+' charge losses' for r in charge_losses_df.columns.to_list()})
    dispatch = dispatch.join(charge_losses_df)

    unserved_df = results['unserved_power'].copy()
    # unserved_df = unserved_df.rename(columns={r: r+' unserved power' for r in unserved_df.columns.to_list()})
    dispatch = dispatch.join(unserved_df)

    return dispatch
