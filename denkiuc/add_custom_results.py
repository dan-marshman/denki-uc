import os
import pandas as pd


def add_custom_results(data, results, results_path):
    new_results = dict()
    
    new_results['charge_losses'] = add_charge_losses(data, results)
    new_results['total_charge_load'] = add_total_charge_load(results, new_results)
    new_results['dispatch'] = add_dispatch_result(data, results, new_results)

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
        charge_losses[col] = charge_losses[col] / (data.units['RTEfficiency'][u]) * (1 - data.units['RTEfficiency'][u])

    return charge_losses


def add_total_charge_load(results, new_results):
    total_charge_load = results['charge_after_losses'].add(new_results['charge_losses'])
    return total_charge_load


def add_dispatch_result(data, results, new_results):
    dispatch = results['power_generated'].copy()
    dispatch = \
        pd.concat([dispatch], axis=1, keys=['generated']).swaplevel(0, 2, axis=1).swaplevel(0, 1, axis=1)

    charge_df = -1 * results['charge_after_losses'].copy()
    charge_df = \
        pd.concat([charge_df], axis=1, keys=['charged']).swaplevel(0, 2, axis=1).swaplevel(0, 1, axis=1)
    dispatch = dispatch.join(charge_df)

    losses_df = -1 * new_results['charge_losses'].copy()
    losses_df = \
        pd.concat([losses_df], axis=1, keys=['losses']).swaplevel(0, 2, axis=1).swaplevel(0, 1, axis=1)
    dispatch = dispatch.join(losses_df)

    dispatch = dispatch.join(-1 * data.traces['demand'])

    unserved_df = results['unserved_power'].copy()
    unserved_df.columns = pd.MultiIndex.from_product([unserved_df.columns, ['Unserved power']])
    dispatch = dispatch.join(unserved_df)

    return dispatch
