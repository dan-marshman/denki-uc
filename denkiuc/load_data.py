import os
import pandas as pd
import logging

module_path = os.path.split(os.path.abspath(__file__))[0]
default_files_path = os.path.join(module_path, 'default_files')


def load_default_file(filename):
    file_path = os.path.join(default_files_path, filename)

    data = pd.read_csv(file_path, index_col=0)

    return data


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
                settings.setdefault(row['Parameter'], bool(row['Value']))

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

    sets['units_commit'] = dkSet('units_commit', units_commit, sets['units'])
    sets['units_storage'] = dkSet('units_storage', units_storage, sets['units'])
    sets['units_variable'] = dkSet('units_variable', units_variable, sets['units'])

    units_inflexible = create_unit_subsets('Inflexible', data, sets['units_commit'])
    units_flexible = create_unit_subsets('Flexible', data, sets['units_commit'])

    sets['units_inflexible'] = dkSet('units_inflexible', units_inflexible, sets['units_commit'])
    sets['units_flexible'] = dkSet('units_flexible', units_flexible, sets['units_commit'])

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


def create_unit_subsets(subset, data, units):
    filename = 'technology_categories.csv'
    path_to_db_tech_cat_file = os.path.join(data.path_to_inputs, filename)

    if os.path.exists(path_to_db_tech_cat_file):
        tech_categories_df = pd.read_csv(path_to_db_tech_cat_file, index_col=0)
    else:
        tech_categories_df = load_default_file(filename)

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
        self.missing_values = dict()

        self.path_to_inputs = path_to_inputs
        self.load_traces()
        self.load_ancillary_service_requirements()
        self.load_unit_data()
        self.load_initial_state()
        self.load_arma_values()

    def load_traces(self):
        self.orig_traces = dict()
        trace_files = ['demand', 'wind', 'solarPV']

        for file in trace_files:
            file_path = os.path.join(self.path_to_inputs, file + '.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, index_col=0)
                self.orig_traces[file] = df
            else:
                print("Looking for trace file - doesn't exist", file_path)
                exit()

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

    def load_arma_values(self):
        filename = 'arma_values.csv'
        path_to_db_arma_file = os.path.join(self.path_to_inputs, filename)
        if os.path.exists(path_to_db_arma_file):
            self.arma_vals_df = pd.read_csv(path_to_db_arma_file, index_col=0)
        else:
            self.arma_vals_df = load_default_file(filename)

    def add_arma_scenarios(self, scenarios, random_seed):
        import numpy as np

        def fill_arma_vals_for_scens_and_ints(scenarios, new_trace, orig_df):
            for scenario in scenarios.indices[1:]:
                new_trace.loc[:, (scenario, region)] = orig_df[region]

                forecast_error = [0] * len(new_trace)

                distribution = np.random.normal(0, arma_sigma, len(new_trace))

                for j, i in enumerate(new_trace.index.to_list()[1:]):
                    forecast_error[j+1] = \
                        arma_alpha * forecast_error[j] \
                        + distribution[j+1] + distribution[j] * arma_beta

                    if trace_name == 'demand':
                        new_trace.loc[i, (scenario, region)] = \
                            (1 + forecast_error[j+1]) * new_trace.loc[i, (0, region)]
                    elif trace_name in ['wind', 'solarPV']:
                        new_trace.loc[i, (scenario, region)] = \
                            forecast_error[j+1] + new_trace.loc[i, (0, region)]

            return new_trace

        def enforce_limits(new_trace, trace_name):
            if trace_name in ['wind', 'solarPV']:
                new_trace = new_trace.clip(lower=0, upper=1)
            if trace_name in ['demand']:
                new_trace = new_trace.clip(lower=0)
            return new_trace

        np.random.seed(random_seed)

        self.traces = dict()

        for trace_name, trace in self.orig_traces.items():
            orig_df = self.orig_traces[trace_name]

            df_cols = pd.MultiIndex.from_product([scenarios.indices, orig_df.columns])
            df_cols = df_cols.set_names(['Scenario', 'Region'])
            new_trace = pd.DataFrame(index=orig_df.index, columns=df_cols)

            arma_alpha = self.arma_vals_df[trace_name]['alpha']
            arma_beta = self.arma_vals_df[trace_name]['beta']
            arma_sigma = self.arma_vals_df[trace_name]['sigma']

            for region in orig_df.columns:
                new_trace.loc[:, (0, region)] = orig_df[region]
                new_trace = fill_arma_vals_for_scens_and_ints(scenarios, new_trace, orig_df)
                new_trace = enforce_limits(new_trace, trace_name)
            new_trace.round(5)

            self.traces[trace_name] = new_trace

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
