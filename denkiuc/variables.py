import pulp as pp


class dkVar():
    def __init__(self, name, units, sets, var_type='C'):
        var_type_dict = {'C': 'Continuous', 'I': 'Integer', 'B': 'Binary'}

        self.name = name
        self.units = units
        self.sets = sets
        self.type = var_type_dict[var_type]
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

    def one_dim_to_df(self):
        import pandas as pd

        values = [self.var[i].value() for i in self.sets_indices]
        self.result_df = pd.Series(data=values, index=self.sets_indices, name=self.name)

    def two_dim_to_df(self, sets_order):
        import pandas as pd

        self.result_df = \
            pd.DataFrame(index=sets_order[0].indices, columns=sets_order[1].indices)
        for x0 in sets_order[0].indices:
            for x1 in sets_order[1].indices:
                self.result_df.loc[x0, x1] = self.var[(x0, x1)].value()

    def three_dim_to_df(self, sets_order):
        import pandas as pd

        iterables = [sets_order[1].indices, sets_order[2].indices]
        iterables_names = [sets_order[1].name, sets_order[2].name]
        df_cols = pd.MultiIndex.from_product(iterables, names=iterables_names)

        self.result_df = pd.DataFrame(index=sets_order[0].indices, columns=df_cols)
        self.result_df.index.name = sets_order[0].name
        for x0 in sets_order[0].indices:
            for x1 in sets_order[1].indices:
                for x2 in sets_order[2].indices:
                    self.result_df.loc[x0, (x1, x2)] = self.var[(x0, x1, x2)].value()

    def four_dim_to_df(self, sets_order):
        import pandas as pd

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

    def get_vars_sets_order(self):
        sets_order = dict()
        for n, set in enumerate(self.sets):
            sets_order[n] = set
        return sets_order

    def to_df(self):
        num_indexes = len(self.sets)
        sets_order = self.get_vars_sets_order()

        if num_indexes == 1:
            self.one_dim_to_df()
        elif num_indexes == 2:
            self.two_dim_to_df(sets_order)
        elif num_indexes == 3:
            self.three_dim_to_df(sets_order)
        elif num_indexes == 4:
            self.four_dim_to_df(sets_order)

        self.result_df.index.name = sets_order[0].name
        self.result_df = self.result_df.fillna(-9999)
        self.result_df = self.result_df.astype(float)

        if self.type == 'Binary' or self.type == 'Integer':
            self.result_df = self.result_df.astype(int)

    def remove_LA_int_from_results(self, main_intervals):
        if 'intervals' not in [setx.name for setx in self.sets]:
            self.result_df_trimmed = self.result_df
            return
        else:
            self.result_df_trimmed = self.result_df.loc[main_intervals]

    def write_to_csv(self, write_dir, removed_LA=False):
        import os

        filename = self.name + '_' + self.units + '.csv'

        if not removed_LA:
            full_write_dir = os.path.join(write_dir, 'LA_kept')
            if not os.path.exists(full_write_dir):
                os.makedirs(full_write_dir)
            write_path = os.path.join(write_dir, 'LA_kept', filename)
            self.result_df.to_csv(write_path)

        if removed_LA:
            full_write_dir = os.path.join(write_dir, 'LA_trimmed')
            if not os.path.exists(full_write_dir):
                os.makedirs(full_write_dir)
            write_path = os.path.join(write_dir, 'LA_trimmed', filename)
            self.result_df_trimmed.to_csv(write_path)
