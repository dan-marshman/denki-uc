import os
import pandas as pd
import logging
import denkiuc.misc_functions as mf

module_path = os.path.split(os.path.abspath(__file__))[0]
default_files_path = os.path.join(module_path, 'default_files')


def load_settings(path_to_inputs):
    import csv

    settings = dict()
    settings_path = os.path.join(path_to_inputs, 'settings.csv')

    with open(settings_path) as f:
        settings_data = csv.DictReader(f)
        for row in settings_data:
            if row['Type'] == 'int':
                settings.setdefault(row['Parameter'], int(row['Value']))

            if row['Type'] == 'bool':
                val = row['Value'].lower()
                if val == 'false':
                    settings.setdefault(row['Parameter'], False)
                elif val == 'true':
                    settings.setdefault(row['Parameter'], True)

            if row['Type'] == 'str':
                settings.setdefault(row['Parameter'], str(row['Value']))

            if row['Type'] == 'float':
                settings.setdefault(row['Parameter'], float(row['Value']))

    if 'OUTPUTS_PATH' not in settings.keys():
        settings['OUTPUTS_PATH'] = os.path.join(os.getcwd(), 'denki-outputs')

    return settings


class dkSet():
    def __init__(self, name, indices, master_set=None):
        self.name = name
        self.indices = indices
        self.subsets = list()

        if master_set is not None:
            self.validate_set(master_set)
            master_set.append_subset(self)

    def validate_set(self, master_set):
        for ind in self.indices:
            if ind not in master_set.indices:
                print('\nMember of set called %s (%s) is not a member' % (self.name, str(ind)),
                      'of the master set %s\n' % master_set.name)
                raise ValueError('Subset validation error')

    def append_subset(self, subset):
        self.subsets.append(subset)


def load_master_sets(data, settings):
    sets = dict()

    sets['intervals'] = dkSet('intervals', data.orig_traces['demand'].index.to_list())
    sets['units'] = dkSet('units', data.units.index.to_list())
    sets['scenarios'] = dkSet('scenarios', list(range(settings['NUM_SCENARIOS'])))

    all_reserve_indices = \
        pd.read_csv(os.path.join(default_files_path, 'all_reserve_indices.csv'))
    reserve_indices = \
        [r for r in all_reserve_indices['ReserveType'] if r in data.reserve_requirement.columns]

    sets['reserves'] = dkSet('reserves', reserve_indices)

    return sets


def load_unit_subsets(data, sets):
    units_commit = create_unit_subsets('Commit', data, sets['units'])
    units_storage = create_unit_subsets('Storage', data, sets['units'])
    units_variable = create_unit_subsets('Variable', data, sets['units'])
    units_renewable = create_unit_subsets('Renewable', data, sets['units'])
    units_thermal = create_unit_subsets('Thermal', data, sets['units'])

    sets['units_commit'] = dkSet('units_commit', units_commit, sets['units'])
    sets['units_storage'] = dkSet('units_storage', units_storage, sets['units'])
    sets['units_variable'] = dkSet('units_variable', units_variable, sets['units'])
    sets['units_renewable'] = dkSet('units_renewable', units_renewable, sets['units'])
    sets['units_thermal'] = dkSet('units_thermal', units_thermal, sets['units'])

    units_inflex = create_unit_subsets('Inflexible', data, sets['units_commit'])
    units_flex = create_unit_subsets('Flexible', data, sets['units_commit'])

    sets['units_inflex'] = dkSet('units_inflex', units_inflex, sets['units_commit'])
    sets['units_flex'] = dkSet('units_flex', units_flex, sets['units_commit'])

    return sets


def add_reserve_subsets(sets):
    raise_reserves = list()
    lower_reserves = list()

    for r in sets['reserves'].indices:
        if 'Raise' in r:
            raise_reserves.append(r)
        elif 'Lower' in r:
            lower_reserves.append(r)
        else:
            print('Member of reserves', r, 'has not been fit into Raise or Lower categories.')

    sets['raise_reserves'] = dkSet('raise_reserves', raise_reserves, sets['reserves'])
    sets['lower_reserves'] = dkSet('lower_reserves', lower_reserves, sets['reserves'])

    return sets


def load_interval_subsets(settings, sets):
    last_main_interval = len(sets['intervals'].indices) - settings['LOOK_AHEAD_INTS'] - 1

    main_intervals = \
        [i for num, i in enumerate(sets['intervals'].indices) if num <= last_main_interval]
    look_ahead_intervals = [i for i in sets['intervals'].indices if i not in main_intervals]

    sets['look_ahead_intervals'] = \
        dkSet('look_ahead_intervals', look_ahead_intervals, sets['intervals'])
    sets['main_intervals'] = dkSet('main_intervals', main_intervals, sets['intervals'])

    return sets


def make_multi_sets(sets):
    m_sets = \
        {
            'in': [sets['intervals']],
            'in_sc': [sets['intervals'], sets['scenarios']],
            'in_sc_un': [sets['intervals'], sets['scenarios'], sets['units']],
            'in_sc_unco': [sets['intervals'], sets['scenarios'], sets['units_commit']],
            'in_sc_unst': [sets['intervals'], sets['scenarios'], sets['units_storage']],
            'in_sc_un_re': [sets['intervals'], sets['scenarios'], sets['units'], sets['reserves']],
            'in_sc_re': [sets['intervals'], sets['scenarios'], sets['reserves']]
        }

    return m_sets


def create_unit_subsets(subset, data, units):
    def read_tech_categories_file():
        filename = 'technology_categories.csv'
        path_to_db_tech_cat_file = os.path.join(data.path_to_inputs, filename)

        if os.path.exists(path_to_db_tech_cat_file):
            tech_categories_df = pd.read_csv(path_to_db_tech_cat_file, index_col=0)
        else:
            tech_categories_df = mf.load_default_file(filename)

        return tech_categories_df

    def add_indices_to_subset():
        subset_indices = []

        for u in units.indices:
            unit_tech = data.units['Technology'][u]
            if tech_categories_df[subset][unit_tech] == 1:
                subset_indices.append(u)

        return subset_indices

    tech_categories_df = read_tech_categories_file()
    subset_indices = add_indices_to_subset()

    return subset_indices


def define_scenario_probability(scenarios):
    scenario_prob = dict()
    for s in scenarios.indices:
        scenario_prob[s] = 1 / len(scenarios.indices)
    return scenario_prob


class Data:
    def __init__(self, path_to_inputs):
        self.missing_values = dict()

        self.path_to_inputs = path_to_inputs
        self.load_traces()
        self.load_ancillary_service_requirements()
        self.load_unit_data()
        self.load_initial_state()
        self.load_arma_values()

    def load_unit_data(self):
        unit_data_path = os.path.join(self.path_to_inputs, 'unit_data.csv')

        if os.path.exists(unit_data_path):
            self.units = pd.read_csv(unit_data_path, index_col=0)

        else:
            print("Looking for unit data file - doesn't exist", unit_data_path)
            exit()

    def load_initial_state(self):
        initial_state_path = os.path.join(self.path_to_inputs, 'initial_state.csv')

        if os.path.exists(initial_state_path):
            self.initial_state = pd.read_csv(initial_state_path, index_col=0)
            self.missing_values['initial_state'] = False

        else:
            print("Looking for initial state file - doesn't exist", initial_state_path)
            self.missing_values['initial_state'] = True

    def validate_initial_state_data(self, sets):
        for u in sets['units_commit'].indices:
            commit_val = self.initial_state['NumCommited'][u]
            units_built_val = self.units['NoUnits'][u]

            if commit_val != int(commit_val):
                logging.error("Initial state had commit value of %f for unit %s" % (commit_val, u),
                              " - changed to %d" % int(commit_val))
                self.initial_state.loc[u, 'NumCommited'] = int(commit_val)

            if commit_val > units_built_val:
                logging.error('Initial state had more units committed (%f) for unit' % commit_val,
                              ' %s than exist (%d).' % (u, units_built_val),
                              ' Changed to %d.' % units_built_val)
                self.initial_state.loc[u, 'NumCommited'] = units_built_val

            if commit_val < 0:
                logging.error('initial state had commit value of',
                              '%f for unit %s.' % (commit_val, u),
                              'Changed to 0.')
                self.initial_state.loc[u, 'NumCommited'] = 0

            initial_power_MW = self.initial_state['PowerGeneration_MW'][u]

            minimum_initial_power_MW = \
                self.initial_state['NumCommited'][u] \
                * self.units['MinGen'][u] * self.units['Capacity_MW'][u]

            maximum_initial_power_MW = \
                self.initial_state['NumCommited'][u] * self.units['Capacity_MW'][u]

            if initial_power_MW < minimum_initial_power_MW:
                print('Unit %s has its initial power < minimum generation based on commitment' % u)

            if initial_power_MW > maximum_initial_power_MW:
                print('Unit %s has initial power > maximum generation based on commitment' % u)

        for u in sets['units_storage'].indices:
            if self.initial_state['StorageLevel_frac'][u] > 1:
                print('Unit %s has initial storage fraction greater than 1' % u)
                exit()

    def load_ancillary_service_requirements(self):
        reserve_requirement_path = os.path.join(self.path_to_inputs, 'reserve_requirement.csv')

        if os.path.exists(reserve_requirement_path):
            self.reserve_requirement = pd.read_csv(reserve_requirement_path, index_col=0)
            self.missing_values['reserve_requirement'] = False

        else:
            print("Looking for reserve_requirement - doesn't exist", reserve_requirement_path)
            self.missing_values['reserve_requirement'] = True

    def add_default_values(self, sets):
        if self.missing_values['reserve_requirement']:
            self.reserve_requirement = \
                pd.DataFrame(0, index=sets['intervals'].indices, columns=sets['reserves'])

    def replace_reserve_requirement_index(self):
        first_trace = list(self.orig_traces.keys())[0]
        self.reserve_requirement.index = self.orig_traces[first_trace].index
