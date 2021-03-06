import os
import pandas as pd
import pulp as pp
import sys

class ucModel():
    def __init__(self, name, path_to_inputs):
        import denkiuc.load_data as ld
        import denkiuc.variables as va

        print()
        print("-------------------------------------------------------------------------")
        print()

        self.name = name
        self.path_to_inputs = path_to_inputs

        print("Initiating UC model called", self.name)
        print("Using database folder located at   ", path_to_inputs)

        if not os.path.exists(self.path_to_inputs):
            print("Inputs path does not exist. Exiting")
            return

        self.data = ld.Data(path_to_inputs)
        self.settings = ld.load_settings(path_to_inputs)
        self.sets = ld.load_master_sets(self.data)
        self.sets = ld.load_unit_subsets(self.data, self.sets)
        self.data.validate_initial_state_data(self.sets)
        
        self.vars = va.make_all_variables(self.sets)
        print(self.vars)

        self.build_model()
        self.solve_model()
        self.store_results()
        self.sanity_check_solution()

        print()
        print("---------------------------- Model generated ----------------------------")

    def build_model(self):
        import denkiuc.constraints as cnsts
        import denkiuc.obj_fn as obj

        self.mod = pp.LpProblem(self.name, sense=pp.LpMinimize)
        self.mod += obj.obj_fn(self.sets, self.data, self.variables.vars, self.settings)

        self.constraints_df = cnsts.create_constraints_df(self.path_to_inputs)
        self.mod = cnsts.add_all_constraints_to_dataframe(self.sets, self.data, self.variables.vars, self.settings, self.mod, self.constraints_df)

    def solve_model(self):
        def exit_if_infeasible(status):
            if status == 'Infeasible':
                print()
                print(self.name, 'was infeasible. Exiting.')
                print()
                exit()

        print('Begin solving the model')
        self.mod.solve(pp.PULP_CBC_CMD(timeLimit=120,
                                  threads=0,
                                  msg=0,
                                  gapRel=0))
        print('Solve complete')

        self.optimality_status = pp.LpStatus[self.mod.status]
        print('Model status: %s' % self.optimality_status)
        exit_if_infeasible(self.optimality_status)

        self.opt_obj_fn_value = self.mod.objective.value()
        print('Objective function = %f' % self.opt_obj_fn_value)
        print()

    def store_results(self):
        import denkiuc.store_results_to_df as sr

        self.results = dict()
        def get_num_of_var_indexes(vars):
            num_indexes = dict()
            for var in vars:
                keys = list(vars[var].keys())
                if type(keys[0]) == tuple:
                    num_indexes[var] = len(keys[0])
                elif type(keys[0]) == int:
                    num_indexes[var] = 1
            return num_indexes

        def store_variable_result(vars):
            num_indexes = get_num_of_var_indexes(self.variables.vars)
            results = dict()

            for key, val in vars.items():
                if num_indexes[key] == 1:
                    indices = list(vars[key].keys())
                    values = [vars[key][i].value() for i in indices]
                    results[key] = pd.Series(data=values, index = indices)
                if num_indexes[key] == 2:
                    print(key)
                    indices = list(vars[key].keys())
                    print(indices)
                    exit()

        self.results = store_variable_result(self.variables.vars)

        exit()
        # self.results['commit_status'] = sr.commit_status_to_df(self)
        # self.results['energy_price_$pMWh'] = sr.energy_price_to_df(self)
        # self.results['charge_after_losses_MW'] = sr.charge_after_losses_to_df(self)
        # self.results['charge_before_losses_MW'] = sr.charge_before_losses_to_df(self)
        # self.results['power_generated_MW'] = sr.power_generated_to_df(self)
        # self.results['unserved_demand_MW'] = sr.unserved_demand_to_df(self)
        # self.results['energy_in_storage_MWh'] = sr.energy_in_storage_to_df(self)

    def sanity_check_solution(self):
        import denkiuc.sanity_check_solution as scs

        scs.check_power_lt_capacity(self)
        scs.total_gen_equals_demand(self)
        scs.check_energy_charged_lt_charge_capacity(self)
        scs.check_storage_continiuity(self)
        scs.check_stored_energy_lt_storage_capacity(self)
