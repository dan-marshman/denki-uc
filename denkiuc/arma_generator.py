import os
import pandas as pd
import denkiuc.misc_functions as mf
import sys


path_to_denki = os.path.dirname(os.path.abspath(__file__))
path_to_examples = os.path.join(os.path.dirname(path_to_denki), 'examples')
path_to_tests = os.path.join(os.path.dirname(path_to_denki), 'test')


def main(paramters):
    trace_locations = load_trace_locations(paramters['INPUT_FOLDER'])
    deterministic_traces = load_deterministic_traces(trace_locations, paramters['INPUT_FOLDER'])
    arma_vals_df = load_arma_values(paramters['INPUT_FOLDER'])
    stochastic_traces = add_arma_scenarios(paramters, deterministic_traces, arma_vals_df)
    write_traces_to_sql(stochastic_traces, paramters)


def load_trace_locations(INPUT_FOLDER):
    arma_locations_path = os.path.join(INPUT_FOLDER, 'arma_trace_locations.csv')
    trace_locations = pd.read_csv(arma_locations_path)
    return trace_locations


def load_deterministic_traces(trace_locations, INPUT_FOLDER):
    deterministic_traces = dict()
    trace_names = trace_locations['TraceName'].to_list()

    for trace_name in trace_names:
        file_path = os.path.join(INPUT_FOLDER, trace_name + '.csv')
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col=0)
            deterministic_traces[trace_name] = df
        else:
            print("Looking for trace file - doesn't exist", file_path)
            exit()

    return deterministic_traces


def load_arma_values(INPUT_FOLDER):
    filename = 'arma_values.csv'
    path_to_db_arma_file = os.path.join(INPUT_FOLDER, filename)

    if os.path.exists(path_to_db_arma_file):
        arma_vals_df = pd.read_csv(path_to_db_arma_file, index_col=0)
    else:
        arma_vals_df = mf.load_default_file(filename)

    return arma_vals_df


def add_arma_scenarios(paramters, deterministic_traces, arma_vals_df):
    import numpy as np

    def fill_arma_vals(scenario_indices, new_traces, deterministic_trace):
        for scenario in scenario_indices[1:]:
            new_traces.loc[:, scenario] = deterministic_trace

            forecast_error = [0] * len(new_traces)

            distribution = np.random.normal(0, arma_sigma, len(new_traces))

            for j, i in enumerate(new_traces.index.to_list()[1:]):
                forecast_error[j+1] = \
                    arma_alpha * forecast_error[j] \
                    + distribution[j+1] + distribution[j] * arma_beta

                if trace_name == 'demand':
                    new_traces.loc[i, scenario] = (1 + forecast_error[j+1]) * new_traces.loc[i, 0]
                elif trace_name in ['wind', 'solarPV']:
                    new_traces.loc[i, scenario] = forecast_error[j+1] + new_traces.loc[i, 0]

        return new_traces

    def enforce_limits(new_traces, trace_name):
        if trace_name in ['wind', 'solarPV']:
            new_traces = new_traces.clip(lower=0, upper=1)
        if trace_name in ['demand']:
            new_traces = new_traces.clip(lower=0)

        return new_traces

    np.random.seed(paramters['RANDOM_SEED'])
    stochastic_traces = dict()
    scenario_indices = list(range(paramters['NUM_SCENARIOS']))

    for trace_name, deterministic_trace in deterministic_traces.items():
        deterministic_trace = deterministic_trace.iloc[:, 0]
        new_traces = pd.DataFrame(index=deterministic_trace.index, columns=scenario_indices)

        arma_alpha = arma_vals_df[trace_name]['alpha']
        arma_beta = arma_vals_df[trace_name]['beta']
        arma_sigma = arma_vals_df[trace_name]['sigma']

        new_traces.loc[:, 0] = deterministic_trace.iloc[0]
        new_traces = fill_arma_vals(scenario_indices, new_traces, deterministic_trace)
        new_traces = enforce_limits(new_traces, trace_name)
        new_traces.round(5)

        stochastic_traces[trace_name] = new_traces

    return stochastic_traces


def write_traces_to_sql(stochastic_traces, paramters):
    import sqlite3

    arma_out_filename = '%03d_arma_traces.db' % paramters['NUM_SCENARIOS']
    arma_out_dir = os.path.join(paramters['INPUT_FOLDER'], 'arma_traces')
    arma_out_path = os.path.join(arma_out_dir, arma_out_filename)
    mf.make_folder(arma_out_dir, keep_existing=True)

    db_connection = sqlite3.connect(arma_out_path)

    for trace_name, traces in stochastic_traces.items():
        traces.to_sql(trace_name, db_connection, if_exists='replace')

    db_connection.close()


def run_arma_model(PATH_TO_INPUTS, NUM_SCENARIOS, RANDOM_SEED=0):

    paramters = \
        {
            'INPUT_FOLDER': PATH_TO_INPUTS,
            'NUM_SCENARIOS': NUM_SCENARIOS,
            'RANDOM_SEED': RANDOM_SEED
         }

    main(paramters)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Not enough arguments. Should be 1) path to folder 2) number of scenarios and 3)",
              " (optional) random seed.")

    PATH_TO_INPUTS = sys.argv[1]
    NUM_SCENARIOS = sys.argv[2]

    if len(sys.argv) > 3:
        RANDOM_SEED = sys.argv[3]
    else:
        RANDOM_SEED = 0

    run_arma_model(PATH_TO_INPUTS, NUM_SCENARIOS, RANDOM_SEED)
