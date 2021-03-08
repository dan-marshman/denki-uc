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
                print("member of set called %s (%s) is not a member of the master set %s" % (self.name, str(ind), master_set.name))
                raise ValueError('Subset validation error')

    def append_subset(self, subset):
        self.subsets.append(subset)


def load_master_sets(data):
    sets = dict()

    sets['intervals'] = dkSet('intervals', data.traces['demand'].index.to_list())
    sets['units'] = dkSet('units', data.units.index.to_list())
       
    return sets


def load_unit_subsets(data, sets):
    sets['units_commit'] = \
        dkSet('units_commit', create_unit_subsets('Commit', data, sets['units']), sets['units'])

    sets['units_storage'] = \
        dkSet('units_storage', create_unit_subsets('Storage', data, sets['units']), sets['units'])

    sets['units_variable'] = \
        dkSet('units_variable', create_unit_subsets('Variable', data, sets['units']), sets['units'])

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


class Data:
    def __init__(self, path_to_inputs):
        self.traces = self.load_traces(path_to_inputs)
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
                print()

        return traces

    def load_unit_data(self, path_to_inputs):
        unit_data_path = os.path.join(path_to_inputs, 'unit_data.csv')

        if os.path.exists(unit_data_path):
            unit_data = pd.read_csv(unit_data_path, index_col=0)

        else:
            print("Looking for unit data file - doesn't exist", file_path)
            print()

        return unit_data

    def load_initial_state(self, path_to_inputs):
        initial_state_path = os.path.join(path_to_inputs, 'initial_state.csv')

        if os.path.exists(initial_state_path):
            initial_state = pd.read_csv(initial_state_path, index_col=0)

        else:
            print("Looking for initial state file - doesn't exist", file_path)
            print()

        return initial_state

    def validate_initial_state_data(self, sets):
        for u in sets['units_commit'].indices:
            commit_val = self.initial_state['Commit'][u]
            if commit_val not in [0, 1]:
                new_commit_val = round(commit_val, 0)
                if new_commit_val > 1:
                    new_commit_val = 1
                if new_commit_val < 0:
                    new_commit_val = 0
                logging.error("initial state had commit value of %f for unit %s. Changed to %d" % (commit_val, u, new_commit_val))
                self.initial_state.loc[u, 'Commit'] = new_commit_val

            initial_power_MW = self.initial_state['PowerGeneration_MW'][u] 
            
            minimum_initial_power_MW = \
                self.initial_state['Commit'][u] * self.units['MinGen'][u] * self.units['Capacity_MW'][u]
            
            maximum_initial_power_MW = \
                self.initial_state['Commit'][u] * self.units['Capacity_MW'][u]

            if  initial_power_MW < minimum_initial_power_MW:
                print('Unit %s has initial power below its minimum generation based on commitment' % u)

            if  initial_power_MW > maximum_initial_power_MW:
                print('Unit %s has initial power above its maximum generation based on commitment' % u)
        
        for u in sets['units_storage'].indices:
            if self.initial_state['StorageLevel_frac'][u] > 1:
                print('Unit %s has initial storage fraction greater than 1' % u)
                exit()
