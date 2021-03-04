import os
import pandas as pd


def load_traces(self):
    trace_files = ['demand',
                   'wind',
                   'solarPV']

    self.traces = dict()

    for file in trace_files:
        file_path = os.path.join(self.path_to_inputs, file + '.csv')
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col=0)
            self.traces[file] = df
        else:
            print("Looking for trace file - doesn't exist", file_path)
            print()
    return self


def load_settings(self):
    import csv

    self.settings = dict()
    settings_path = os.path.join(self.path_to_inputs, 'settings.csv')

    f = open(settings_path)
    settings_data = csv.DictReader(f)
    for row in settings_data:
        self.settings.setdefault(row['Parameter'], row['Value'])
    f.close
    print(self.settings)
    self.settings['INTERVALS_PER_HOUR'] = int(self.settings['INTERVALS_PER_HOUR'])
    self.settings['UNS_LOAD_PNTY'] = int(self.settings['UNS_LOAD_PNTY'])
    self.settings['UNS_RESERVE_PNTY'] = int(self.settings['UNS_RESERVE_PNTY'])
    self.settings['UNS_INERTIA_PNTY'] = int(self.settings['UNS_INERTIA_PNTY'])
    return self


def load_unit_data(self):
    unit_data_path = os.path.join(self.path_to_inputs, 'unit_data.csv')
    if os.path.exists(unit_data_path):
        self.unit_data = pd.read_csv(unit_data_path, index_col=0)
    else:
        print("Looking for unit data file - doesn't exist", file_path)
        print()
    return self


def create_sets(self):
    def assess_category(category):
        module_path = os.path.split(os.path.abspath(__file__))[0]
        path_to_tech_categories_file = os.path.join(module_path, 'technology_categories.csv') 
        tech_categories_df = pd.read_csv(path_to_tech_categories_file, index_col=0)
        subset = []
        for u in self.sets['units']:
            unit_tech = self.unit_data['Technology'][u]
            if tech_categories_df[category][unit_tech] == 1:
                subset.append(u)
        return subset

    self.sets = dict()

    self.sets['intervals'] = self.traces['demand'].index.to_list()
    self.sets['units'] = self.unit_data.index.to_list()

    self.sets['units_commit'] = assess_category('Commit')
    self.sets['units_storage'] = assess_category('Storage')
    self.sets['units_variable'] = assess_category('Variable')
    return self


def load_initial_state(self):
    initial_state_path = os.path.join(self.path_to_inputs, 'initial_state.csv')
    if os.path.exists(initial_state_path):
        self.initial_state = pd.read_csv(initial_state_path, index_col=0)
        validate_initial_state_data(self)
    else:
        print("Looking for initial state file - doesn't exist", file_path)
        print()
    return self


def validate_initial_state_data(self):
    for u in self.sets['units_commit']:
        initial_power_MW = self.initial_state['PowerGeneration_MW'][u] 
        
        minimum_initial_power_MW = \
            self.initial_state['Commit'][u] * self.unit_data['MinGen'][u] * self.unit_data['Capacity_MW'][u]
        
        maximum_initial_power_MW = \
            self.initial_state['Commit'][u] * self.unit_data['Capacity_MW'][u]

        if  initial_power_MW < minimum_initial_power_MW:
            print()
            print('Unit %s has initial power below its minimum generation based on commitment' % u)
            print()
            exit()

        if  initial_power_MW > maximum_initial_power_MW:
            print()
            print('Unit %s has initial power above its maximum generation based on commitment' % u)
            print()
            exit()
    
    for u in self.sets['units_storage']:
        if self.initial_state['StorageLevel_frac'][u] > 1:
            print()
            print('Unit %s has initial storage fraction greater than 1' % u)
            print()
            exit()
