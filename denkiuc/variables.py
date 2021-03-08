import pulp as pp


def make_all_variables(sets):
    
    vars = dict()    

    intervals_units = [sets['intervals'], sets['units']]
    vars['power_generated'] =dkVariable('power_generated', 'MW', intervals_units)
    vars['reserve_enablement'] =dkVariable('reserve_enablement', 'MW', intervals_units)
    
    intervals_units_commit = [sets['intervals'], sets['units_commit']]
    vars['commit_status'] =dkVariable('commit_status', 'Binary', intervals_units_commit, 'Binary')
    vars['inertia_provided'] =dkVariable('inertia_provided', 'MW.s', intervals_units_commit)
    vars['shut_down_status'] =dkVariable('shut_down_status', 'Binary', intervals_units_commit, 'Binary')
    vars['start_up_status'] =dkVariable('start_up_status', 'Binary', intervals_units_commit, 'Binary')
    
    intervals_units_storage = [sets['intervals'], sets['units_storage']]
    vars['charge_after_losses'] =dkVariable('charge_after_losses', 'MW', intervals_units_storage)
    vars['energy_in_reservoir'] =dkVariable('energy_in_reservoir', 'MWh', intervals_units_storage)
    
    vars['unserved_inertia'] =dkVariable('unserved_inertia', 'MW.s', [sets['intervals']])
    vars['unserved_power'] =dkVariable('unserved_power', 'MW', [sets['intervals']])
    vars['unserved_reserve'] =dkVariable('unserved_reserve', 'MW', [sets['intervals']])
    
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

    # def dkSum(self, name_of_set_to_sum):
        # # print(self.sets_indices)
        # # print(self.sets)
        # print()
        # print(self.name)

        # for pos, set in enumerate(self.sets):
            # if set.name == name_of_set_to_sum:
                # set_to_sum = set
        # print(set_to_sum.indices, pos)
        # sum_indices = set_to_sum.indices.copy()
        # sum_list = [self.var[(i)] for i in set_to_sum.indices]
        # print(sum_list)

        # exit()
        # summed_set = pp.lpSum()

    def to_df(self):
        import pandas as pd

        num_indexes = len(self.sets)
        
        results = dict()
        
        sets_order = dict()
        for n, set in enumerate(self.sets):
            sets_order[n] = set

        if num_indexes == 1:
            values = [self.var[i].value() for i in self.sets_indices]
            self.result_df = pd.Series(data=values, index = self.sets_indices, name=self.name)
            

        if num_indexes == 2:
            self.result_df = pd.DataFrame(index=sets_order[0].indices, columns=sets_order[1].indices)
            for x0 in sets_order[0].indices:
                for x1 in sets_order[1].indices:
                    self.result_df.loc[x0, x1] = self.var[(x0, x1)].value()
        
        if num_indexes == 3:
            iterables = [sets_order[1].indices, sets_order[2].indices]
            df_cols = pd.MultiIndex.from_product(iterables)
            self.result_df = pd.DataFrame(index=sets_order[0].indices, columns = df_cols)
            for x0 in sets_order[0].indices:
                for x1 in sets_order[1].indices:
                    for x2 in sets_order[2].indices:
                        self.result_df.loc[x0, (x1, x0)] = self.var[(x0, x1, x2)].value()

        self.result_df.index.name = sets_order[0].name
        self.result_df = self.result_df.astype(float)
        if self.type == 'Binary':
            self.result_df = self.result_df.astype(int)

    def write_to_file(self, write_dir):
        import os

        filename = self.name + '_' + self.units + '.csv'
        write_path = os.path.join(write_dir, filename)
        self.result_df.to_csv(write_path)
