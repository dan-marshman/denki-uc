import os
import pandas as pd
import logging

def load_settings(path_to_inputs):
    import csv

    settings = dict()
    settings_path = os.path.join(path_to_inputs, 'settings.csv')

    with open(settings_path) as f:
        settings_data = csv.DictReader(f)
        for row in settings_data:
            settings.setdefault(row['Parameter'], row['Value'])
    
    settings['INTERVALS_PER_HOUR'] = int(settings['INTERVALS_PER_HOUR'])
    settings['UNS_LOAD_PNTY'] = int(settings['UNS_LOAD_PNTY'])
    settings['UNS_RESERVE_PNTY'] = int(settings['UNS_RESERVE_PNTY'])
    settings['UNS_INERTIA_PNTY'] = int(settings['UNS_INERTIA_PNTY'])
    settings['LOOK_AHEAD_INTS'] = int(settings['LOOK_AHEAD_INTS'])
    settings['NUM_SCENARIOS'] = int(settings['NUM_SCENARIOS'])
    settings['RANDOM_SEED'] = int(settings['RANDOM_SEED'])

    settings['WRITE_RESULTS_WITH_LOOK_AHEAD'] = bool(settings['WRITE_RESULTS_WITH_LOOK_AHEAD'])
    settings['WRITE_RESULTS_WITHOUT_LOOK_AHEAD'] = bool(settings['WRITE_RESULTS_WITHOUT_LOOK_AHEAD'])

    if 'OUTPUTS_PATH' not in settings.keys():
        settings['OUTPUTS_PATH'] = os.path.join(os.getcwd(), 'denki-outputs')

    return settings

class dkSet():
    def __init__(self, name, indices, master_set=None):
        self.name = name
        self.indices = indices

        if master_set != None:
            self.validate_set(master_set)
            master_set.append_subset(self)
        elif master_set == None:
            self.subsets = list()

    def validate_set(self, master_set):
        for ind in self.indices:
            if ind not in master_set.indices:
                print("\nMember of set called %s (%s) is not a member of the master set %s\n" % (self.name, str(ind), master_set.name))
                raise ValueError('Subset validation error')

    def append_subset(self, subset):
        self.subsets.append(subset)


def load_master_sets(data, settings):
    sets = dict()

    sets['intervals'] = dkSet('intervals', data.orig_traces['demand'].index.to_list())
    sets['units'] = dkSet('units', data.units.index.to_list())
    sets['scenarios'] = dkSet('scenarios', list(range(settings['NUM_SCENARIOS'])))
        
       
    return sets


def load_unit_subsets(data, sets):
    units_commit = create_unit_subsets('Commit', data, sets['units'])
    units_storage = create_unit_subsets('Storage', data, sets['units'])
    units_variable = create_unit_subsets('Variable', data, sets['units'])

    sets['units_commit'] = dkSet('units_commit', units_commit, sets['units'])
    sets['units_storage'] = dkSet('units_storage', units_storage, sets['units'])
    sets['units_variable'] = dkSet('units_variable', units_variable, sets['units'])

    return sets


def load_interval_subsets(settings, sets):
    last_main_interval = len(sets['intervals'].indices) - settings['LOOK_AHEAD_INTS'] - 1

    main_intervals = [i for num, i in enumerate(sets['intervals'].indices) if num <= last_main_interval]
    look_ahead_intervals = [i for i in sets['intervals'].indices if i not in main_intervals]

    sets['look_ahead_intervals'] = dkSet('look_ahead_intervals', look_ahead_intervals, sets['intervals'])
    sets['main_intervals'] = dkSet('main_intervals', main_intervals, sets['intervals'])

    return sets


def create_unit_subsets(subset, data, units):
    module_path = os.path.split(os.path.abspath(__file__))[0]
    path_to_tech_categories_file = os.path.join(module_path, 'technology_categories.csv') 
    tech_categories_df = pd.read_csv(path_to_tech_categories_file, index_col=0)
    
    subset_list = []

    for u in units.indices:
        unit_tech = data.units['Technology'][u]
        if tech_categories_df[subset][unit_tech] == 1:
            subset_list.append(u)

    return subset_list


def define_scenario_probability(scenarios):
    scenario_prob = dict()
    for s in scenarios.indices:
        scenario_prob[s] = 1 / len(scenarios.indices)
    return scenario_prob


class Data:
    def __init__(self, path_to_inputs):
        self.orig_traces = self.load_traces(path_to_inputs)
        self.units = self.load_unit_data(path_to_inputs)
        self.initial_state = self.load_initial_state(path_to_inputs)

    def load_traces(self, path_to_inputs):
        traces = dict()
        trace_files = ['demand', 'wind', 'solarPV']

        for file in trace_files:
            file_path = os.path.join(path_to_inputs, file + '.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, index_col=0)
                traces[file] = df
            else:
                print("Looking for trace file - doesn't exist", file_path)
                exit()

        return traces

    def load_unit_data(self, path_to_inputs):
        unit_data_path = os.path.join(path_to_inputs, 'unit_data.csv')

        if os.path.exists(unit_data_path):
            unit_data = pd.read_csv(unit_data_path, index_col=0)

        else:
            print("Looking for unit data file - doesn't exist", unit_data_path)
            exit()

        return unit_data

    def load_initial_state(self, path_to_inputs):
        initial_state_path = os.path.join(path_to_inputs, 'initial_state.csv')

        if os.path.exists(initial_state_path):
            initial_state = pd.read_csv(initial_state_path, index_col=0)

        else:
            print("Looking for initial state file - doesn't exist", initial_state_path)
            exit()

        return initial_state

    def validate_initial_state_data(self, sets):
        for u in sets['units_commit'].indices:
            commit_val = self.initial_state['NumCommited'][u]
            units_built_val = self.units['NoUnits'][u]

            if commit_val != int(commit_val):
                logging.error("initial state had commit value of %f for unit %s." % (commit_val, u),
                    "Changed to %d" % int(commit_val))
                self.initial_state.loc[u, 'NumCommited'] = int(commit_val)

            if commit_val > units_built_val: 
                logging.error("initial state had more units committed (%f) for unit %s than exist" % (commit_val, u),
                    "(%d). Changed to %d." % (units_built_val, units_built_val))
                self.initial_state.loc[u, 'NumCommited'] = units_built_val

            if commit_val < 0:
                logging.error("initial state had commit value of %f for unit %s." % (commit_val, u),
                    "Changed to 0")
                self.initial_state.loc[u, 'NumCommited'] = 0

            initial_power_MW = self.initial_state['PowerGeneration_MW'][u] 
            
            minimum_initial_power_MW = \
                self.initial_state['NumCommited'][u] * self.units['MinGen'][u] * self.units['Capacity_MW'][u]
            
            maximum_initial_power_MW = \
                self.initial_state['NumCommited'][u] * self.units['Capacity_MW'][u]

            if  initial_power_MW < minimum_initial_power_MW:
                print('Unit %s has initial power below its minimum generation based on commitment' % u)

            if  initial_power_MW > maximum_initial_power_MW:
                print('Unit %s has initial power above its maximum generation based on commitment' % u)
        
        for u in sets['units_storage'].indices:
            if self.initial_state['StorageLevel_frac'][u] > 1:
                print('Unit %s has initial storage fraction greater than 1' % u)
                exit()
 
    def add_arma_scenarios(self, scenarios, random_seed):
        import numpy as np

        np.random.seed(random_seed)

        self.traces = dict()

        module_path = os.path.split(os.path.abspath(__file__))[0]
        path_to_arma_vals = os.path.join(module_path, 'arma_values.csv') 
        arma_vals_df = pd.read_csv(path_to_arma_vals, index_col=0)

        for trace_name, trace in self.orig_traces.items():
            orig_df = self.orig_traces[trace_name]

            df_cols = pd.MultiIndex.from_product([scenarios.indices, orig_df.columns])
            df_cols = df_cols.set_names(['Scenario', 'Region'])
            new_trace = pd.DataFrame(index=orig_df.index, columns = df_cols)

            arma_alpha = arma_vals_df[trace_name]['alpha']
            arma_beta = arma_vals_df[trace_name]['beta']
            arma_sigma = arma_vals_df[trace_name]['sigma']

            for region in orig_df.columns:
                new_trace.loc[:, (0, region)] = orig_df[region]
                for scenario in scenarios.indices[1:]:
                    new_trace.loc[:, (scenario, region)] = orig_df[region]

                    forecast_error = [0] * len(new_trace)

                    distribution = np.random.normal(0, arma_sigma, len(new_trace))

                    for i in new_trace.index.to_list()[1:]:
                        forecast_error[i] = \
                            arma_alpha * forecast_error[i-1] + distribution[i] + distribution[i-1] * arma_beta
                        if trace_name == 'demand':
                            new_trace.loc[i, (scenario, region)] = \
                                (1 + forecast_error[i]) * new_trace.loc[i, (0, region)]
                        else:
                            new_trace.loc[i, (scenario, region)] = \
                                min(1, max(0, forecast_error[i] + new_trace.loc[i, (0, region)]))
            new_trace.round(5)
            
            self.traces[trace_name] = new_trace
