import pulp as pp


def make_all_variables(sets):
    vars = dict()

    intervals_units = [sets['intervals'], sets['scenarios'], sets['units']]
    vars['power_generated'] = dkVariable('power_generated', 'MW', intervals_units)

    intervals_units_commit = [sets['intervals'], sets['scenarios'], sets['units_commit']]
    vars['num_commited'] = \
        dkVariable('num_commited', 'NumUnits', intervals_units_commit, 'Integer')
    vars['inertia_provided'] = \
        dkVariable('inertia_provided', 'MW.s', intervals_units_commit)
    vars['is_committed'] = \
        dkVariable('is_committed', 'Binary', intervals_units_commit, 'Binary')
    vars['num_shutting_down'] = \
        dkVariable('num_shutting_down', 'NumUnits', intervals_units_commit, 'Integer')
    vars['num_starting_up'] = \
        dkVariable('num_starting_up', 'NumUnits', intervals_units_commit, 'Integer')

    intervals_units_reserves = \
        [sets['intervals'], sets['scenarios'], sets['units'], sets['reserves']]
    vars['reserve_enabled'] = \
        dkVariable('reserve_enabled', 'MW', intervals_units_reserves)

    intervals_units_storage = [sets['intervals'], sets['scenarios'], sets['units_storage']]
    vars['charge_after_losses'] = dkVariable('charge_after_losses', 'MW', intervals_units_storage)
    vars['energy_in_reservoir'] = dkVariable('energy_in_reservoir', 'MWh', intervals_units_storage)

    vars['unserved_inertia'] = dkVariable('unserved_inertia', 'MW.s', [sets['intervals']])
    vars['unserved_power'] = \
        dkVariable('unserved_power', 'MW', [sets['intervals'], sets['scenarios']])

    intervals_scenarios_reserves = [sets['intervals'], sets['scenarios'], sets['reserves']]
    vars['unserved_reserve'] = dkVariable('unserved_reserve', 'MW', intervals_scenarios_reserves)

    return vars


class dkVariable():
    def __init__(self, name, units, sets, var_type='Continuous'):
        self.name = name
        self.units = units
        self.sets = sets
        self.type = var_type
        self.sets_indices = self.make_var_indices(sets)
        self.var = self.make_pulp_variable(self.sets_indices)

    def make_var_indices(self, sets):
        import itertools

        list_of_set_indices = [x.indices for x in self.sets]

        next_set = list_of_set_indices.pop(0)
        indices_permut = itertools.product(next_set)
        indices_permut_list = [x[0] for x in indices_permut]

        for n in range(len(list_of_set_indices)):
            next_set = list_of_set_indices.pop(0)
            indices_permut = itertools.product(indices_permut_list, next_set)
            indices_permut_list = list(indices_permut)

            if n > 0:
                temp_list = list()
                for x in indices_permut_list:
                    xlist = list(x[0])
                    xlist.append(x[1])
                    temp_list.append(tuple(xlist))
                indices_permut_list = temp_list

        return indices_permut_list

    def make_pulp_variable(self, sets_indices):
        var = pp.LpVariable.dicts(self.name,
                                  (ind for ind in sets_indices),
                                  lowBound=0,
                                  cat=self.type)
        return var

    def to_df(self):
        import pandas as pd

        num_indexes = len(self.sets)

        sets_order = dict()
        for n, set in enumerate(self.sets):
            sets_order[n] = set

        if num_indexes == 1:
            values = [self.var[i].value() for i in self.sets_indices]
            self.result_df = pd.Series(data=values, index=self.sets_indices, name=self.name)

        if num_indexes == 2:
            self.result_df = \
                pd.DataFrame(index=sets_order[0].indices, columns=sets_order[1].indices)
            for x0 in sets_order[0].indices:
                for x1 in sets_order[1].indices:
                    self.result_df.loc[x0, x1] = self.var[(x0, x1)].value()

        if num_indexes == 3:
            iterables = [sets_order[1].indices, sets_order[2].indices]
            iterables_names = [sets_order[1].name, sets_order[2].name]
            df_cols = pd.MultiIndex.from_product(iterables, names=iterables_names)

            self.result_df = pd.DataFrame(index=sets_order[0].indices, columns=df_cols)
            self.result_df.index.name = sets_order[0].name
            for x0 in sets_order[0].indices:
                for x1 in sets_order[1].indices:
                    for x2 in sets_order[2].indices:
                        self.result_df.loc[x0, (x1, x2)] = self.var[(x0, x1, x2)].value()

        if num_indexes == 4:
            iterables = [sets_order[1].indices, sets_order[2].indices, sets_order[3].indices]
            iterables_names = [sets_order[1].name, sets_order[2].name, sets_order[3].name]
            df_cols = pd.MultiIndex.from_product(iterables, names=iterables_names)

            self.result_df = pd.DataFrame(index=sets_order[0].indices, columns=df_cols)
            self.result_df.index.name = sets_order[0].name
            for x0 in sets_order[0].indices:
                for x1 in sets_order[1].indices:
                    for x2 in sets_order[2].indices:
                        for x3 in sets_order[3].indices:
                            self.result_df.loc[x0, (x1, x2, x3)] = \
                                self.var[(x0, x1, x2, x3)].value()

        self.result_df.index.name = sets_order[0].name
        self.result_df = self.result_df.astype(float)
        if self.type == 'Binary' or self.type == 'Integer':
            self.result_df = self.result_df.astype(int)

    def remove_look_ahead_int_from_results(self, main_intervals):
        if 'intervals' not in [setx.name for setx in self.sets]:
            self.result_df_trimmed = self.result_df
            return
        else:
            self.result_df_trimmed = self.result_df.loc[main_intervals]

    def write_to_file(self, write_dir, removed_la=False):
        import os

        filename = self.name + '_' + self.units + '.csv'

        if not removed_la:
            full_write_dir = os.path.join(write_dir, 'look_ahead_kept')
            if not os.path.exists(full_write_dir):
                os.makedirs(full_write_dir)
            write_path = os.path.join(write_dir, 'look_ahead_kept', filename)
            self.result_df.to_csv(write_path)
        if removed_la:
            full_write_dir = os.path.join(write_dir, 'look_ahead_trimmed')
            if not os.path.exists(full_write_dir):
                os.makedirs(full_write_dir)
            write_path = os.path.join(write_dir, 'look_ahead_trimmed', filename)
            self.result_df_trimmed.to_csv(write_path)
