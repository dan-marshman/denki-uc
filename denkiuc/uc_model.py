import os
import pandas as pd
import pulp as pp
import sys

path_to_denki = os.path.split(os.path.abspath(__file__))[0]
print(path_to_denki)

class ucModel():
    def __init__(self, name, path_to_inputs):
        import denkiuc.load_data as ld
        import denkiuc.variables as va

        print()
        print("-------------------------------------------------------------------------")
        print()

        self.name = name
        self.path_to_inputs = path_to_inputs
        self.results = dict()

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
        
        self.path_to_outputs = os.path.join(self.settings['OUTPUTS_PATH'], self.name)

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
        self.mod += obj.obj_fn(self.sets, self.data, self.vars, self.settings)

        self.constraints_df = cnsts.create_constraints_df(self.path_to_inputs)
        self.mod = cnsts.add_all_constraints_to_dataframe(self.sets, self.data, self.vars, self.settings, self.mod, self.constraints_df)

    def solve_model(self):
        def exit_if_infeasible(status):
            if status == 'Infeasible':
                print()
                print(self.name, 'was infeasible. Exiting.')
                print()

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
        import shutil
        import denkiuc.add_custom_results as acs
        
        path_to_results = os.path.join(self.path_to_outputs, 'results')

        if os.path.exists(self.path_to_outputs):
            shutil.rmtree(self.path_to_outputs)

        os.makedirs(path_to_results)
        
        for name, dkvar in self.vars.items():
            dkvar.to_df()
            dkvar.write_to_file(path_to_results)
            self.results[dkvar.name] = dkvar.result_df

        self.results = acs.add_custom_results(self.data, self.results, path_to_results) 

    def sanity_check_solution(self):
        import denkiuc.sanity_check_solution as scs

        scs.run_sanity_checks(self.sets, self.data, self.results)
