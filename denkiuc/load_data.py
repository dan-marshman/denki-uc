import os
import pandas as pd
import logging
import denkiuc.misc_functions as mf

module_path = os.path.split(os.path.abspath(__file__))[0]
default_files_path = os.path.join(module_path, 'default_files')


def load_settings(paths):
    import csv

    settings = dict()

    with open(paths['settings']) as f:
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

    sets['intervals'] = dkSet('intervals', data.traces['demand'].index.to_list())
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
        data.paths['tech_cat_file'] = os.path.join(data.paths['inputs'], filename)

        if os.path.exists(data.paths['tech_cat_file']):
            tech_categories_df = pd.read_csv(data.paths['tech_cat_file'], index_col=0)
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
    def __init__(self, path_to_inputs, settings):
        self.missing_values = dict()
        self.traces = dict()

        self.paths = {'inputs': path_to_inputs}
        self.num_scenarios = settings['NUM_SCENARIOS']
        self.load_stochastic_traces(settings)
        self.load_ancillary_service_requirements()
        self.load_unit_data()
        self.load_initial_state()

    def load_stochastic_traces(self, settings):
        import denkiuc.arma_generator as ag
        import sqlite3

        arma_out_dir = os.path.join(self.paths['inputs'], 'arma_traces')

        def check_if_new_arma_db_needed():
            arma_dbs = os.listdir(arma_out_dir)

            if len(arma_dbs) == 0:
                ag.run_arma_model(self.paths['inputs'],
                                  settings['NUM_SCENARIOS'],
                                  settings['RANDOM_SEED'])
                return

            max_scenario_db = max([int(f[0:3]) for f in arma_dbs])
            if settings['NUM_SCENARIOS'] > max_scenario_db:
                ag.run_arma_model(self.paths['inputs'],
                                  settings['NUM_SCENARIOS'],
                                  settings['RANDOM_SEED'])

        def find_arma_db():
            for db_file in os.listdir(arma_out_dir):
                if int(db_file[0:3]) >= settings['NUM_SCENARIOS']:
                    return db_file

        check_if_new_arma_db_needed()
        db_file = find_arma_db()
        arma_db_path = os.path.join(arma_out_dir, db_file)

        db_connection = sqlite3.connect(arma_db_path)
        for trace_name in ['wind', 'solarPV', 'demand']:
            query = 'select * from %s' % trace_name
            self.traces[trace_name] = pd.read_sql_query(query, db_connection, index_col='Interval')
            self.traces[trace_name].columns = self.traces[trace_name].columns.map(int)
        db_connection.close()

    def load_unit_data(self):
        self.paths['unit_data'] = os.path.join(self.paths['inputs'], 'unit_data.csv')

        if os.path.exists(self.paths['unit_data']):
            self.units = pd.read_csv(self.paths['unit_data'], index_col=0)

        else:
            print("Looking for unit data file - doesn't exist", self.paths['unit_data'])
            exit()

    def load_initial_state(self):
        initial_state_path = os.path.join(self.paths['inputs'], 'initial_state.csv')

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
                * self.units['MinGen_pctCap'][u] * self.units['Capacity_MW'][u]

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
        reserve_requirement_path = os.path.join(self.paths['inputs'], 'reserve_requirement.csv')

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
        first_trace = list(self.traces.keys())[0]
        self.reserve_requirement.index = self.traces[first_trace].index
