import denkiuc.load_data as ld
import denkiuc.misc_functions as mf
import denkiuc.variables as va
import os
import pandas as pd
import pulp as pp
import sys


class ucModel():
    def __init__(self, name, path_to_inputs):
        import shutil

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

        self.setup()
        self.data = ld.Data(path_to_inputs)
        self.sets = ld.load_master_sets(self.data)
        self.sets = ld.load_unit_subsets(self.data, self.sets)
        self.data.validate_initial_state_data(self.sets)
        self.vars = va.make_all_variables(self.sets)

        self.build_model()

        print("\n---- Model built ----\n")

    def setup(self):
        self.settings = ld.load_settings(self.path_to_inputs)
        self.path_to_outputs = os.path.join(self.settings['OUTPUTS_PATH'], self.name)
        mf.make_outputs_folder(self.path_to_outputs)
        mf.set_logger_path(self.path_to_outputs)
        self.results = dict()

    def solve(self):
        self.solve_model()
        self.store_results()
        self.sanity_check_solution()

        print("\n---- Model solved ----\n")

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
                print("\n", self.name, 'was infeasible. Exiting.')

        print('Begin solving the model')
        self.mod.solve(pp.PULP_CBC_CMD(timeLimit=120,
                                  threads=0,
                                  msg=0,
                                  gapRel=0))

        self.optimality_status = pp.LpStatus[self.mod.status]
        print('Model status: %s' % self.optimality_status)
        exit_if_infeasible(self.optimality_status)

        self.opt_obj_fn_value = self.mod.objective.value()
        print('Objective function = %f' % self.opt_obj_fn_value)

    def store_results(self):
        import shutil
        import denkiuc.add_custom_results as acs

        path_to_results = os.path.join(self.path_to_outputs, 'results')

        os.makedirs(path_to_results)

        for name, dkvar in self.vars.items():
            dkvar.to_df()
            dkvar.write_to_file(path_to_results)
            self.results[dkvar.name] = dkvar.result_df

        self.results = acs.add_custom_results(self.data, self.results, path_to_results) 

    def sanity_check_solution(self):
        import denkiuc.sanity_check_solution as scs

        scs.run_sanity_checks(self.sets, self.data, self.results)


path_to_denki = os.path.dirname(os.path.abspath(__file__))
path_to_examples = os.path.join(os.path.dirname(path_to_denki), 'examples')
path_to_tests = os.path.join(os.path.dirname(path_to_denki), 'test')


if __name__ == '__main__':
    name = sys.argv[1]
    path_to_inputs = sys.argv[2]
    model = ucModel(name, path_to_inputs)
