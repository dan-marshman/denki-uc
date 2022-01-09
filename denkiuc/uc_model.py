import denkiuc.denki_paths
import denkiuc.load_data as ld
import denkiuc.misc_functions as mf
import denkiuc.variables as va
import os
import pulp as pp
import sys


class ucModel():
    def __init__(self, name, path_to_inputs):
        self.name = name
        self.paths = denkiuc.denki_paths.dk_paths
        self.paths = {'inputs': path_to_inputs}

    def prepare_model(self):
        mf.check_input_dir_exists(self.paths['inputs'])
        self.load_settings()
        self.load_data()
        self.arrange_sets_and_data()
        self.init_results_dict()
        self.add_variables()
        self.build_model()

    def load_settings(self):
        self.paths['settings'] = os.path.join(self.paths['inputs'], 'settings.csv')
        self.settings = ld.load_settings(self.paths)
        self.paths['outputs'] = os.path.join(self.settings['OUTPUTS_PATH'], self.name)
        mf.make_folder(self.paths['outputs'])
        mf.set_logger_path(self.paths['outputs'])

    def load_data(self):
        self.data = ld.Data(self.paths['inputs'], self.settings)

    def arrange_sets_and_data(self):
        self.sets = ld.load_master_sets(self.data, self.settings)
        self.sets = ld.load_unit_subsets(self.data, self.sets)
        self.sets = ld.add_reserve_subsets(self.sets)
        self.sets = ld.load_interval_subsets(self.settings, self.sets)
        self.m_sets = ld.make_multi_sets(self.sets)

        self.data.probability_of_scenario = ld.define_scenario_probability(self.sets['scenarios'])

        if not self.data.missing_values['initial_state']:
            self.data.validate_initial_state_data(self.sets)

        self.data.add_default_values(self.sets)
        self.data.replace_reserve_requirement_index()

        print("\nParameters and sets are ready")

    def init_results_dict(self):
        self.results = dict()

    def add_variables(self):
        vars = dict()
        m_sets = self.m_sets

        vars['power_generated'] = va.dkVar('power_generated', 'MW', m_sets['in_sc_un'])

        vars['num_committed'] = va.dkVar('num_committed', 'NumUnits', m_sets['in_sc_unco'], 'I')
        vars['inertia_provided'] = va.dkVar('inertia_provided', 'MW.s', m_sets['in_sc_unco'])
        vars['is_committed'] = va.dkVar('is_committed', 'Binary', m_sets['in_sc_unco'], 'B')
        vars['num_shutting_down'] = \
            va.dkVar('num_shutting_down', 'NumUnits', m_sets['in_sc_unco'], 'I')
        vars['num_starting_up'] = \
            va.dkVar('num_starting_up', 'NumUnits', m_sets['in_sc_unco'], 'I')

        vars['reserve_enabled'] = va.dkVar('reserve_enabled', 'MW', m_sets['in_sc_un_re'])

        vars['charge_after_losses'] = va.dkVar('charge_after_losses', 'MW', m_sets['in_sc_unst'])
        vars['energy_in_reservoir'] = va.dkVar('energy_in_reservoir', 'MWh', m_sets['in_sc_unst'])

        vars['unserved_inertia'] = va.dkVar('unserved_inertia', 'MW.s', m_sets['in'])

        vars['unserved_power'] = va.dkVar('unserved_power', 'MW', m_sets['in_sc'])

        vars['unserved_reserve'] = va.dkVar('unserved_reserve', 'MW', m_sets['in_sc_re'])

        self.vars = vars

    def run_model(self):
        from denkiuc.add_custom_results import add_final_state
        import sqlite3

        self.solve_model()
        self.store_results()

        self.final_state = add_final_state(self.data, self.vars, self.sets, self.paths)

        self.paths['final_state'] = os.path.join(self.paths['results'], 'final_state.db')
        connection = sqlite3.connect(self.paths['final_state'])
        for name, series in self.final_state.items():
            series.to_sql(name, connection)

        connection.close()
        print("Final state db written")

    def build_model(self):
        import denkiuc.constraints as cnts
        import denkiuc.obj_fn as obj

        self.mod = pp.LpProblem(self.name, sense=pp.LpMinimize)
        self.mod += obj.obj_fn(self.sets, self.data, self.vars, self.settings)

        self.cnts_df = cnts.create_cnts_df(self.paths['inputs'])
        self.mod = cnts.add_all_constraints_to_dataframe(self.sets,
                                                         self.data,
                                                         self.vars,
                                                         self.settings,
                                                         self.mod,
                                                         self.cnts_df)

    def solve_model(self):
        import time

        print('Begin solving the model\nOptimising...')

        time_start_solve = time.perf_counter()

        self.mod.solve(pp.PULP_CBC_CMD(timeLimit=5,
                                       threads=0,
                                       msg=0,
                                       gapRel=0.01))

        print("Finished optimising\n")

        time_end_solve = time.perf_counter()
        self.solver_time = time_end_solve - time_start_solve

        self.optimality_status = pp.LpStatus[self.mod.status]
        print('Model status: %s' % self.optimality_status)
        mf.exit_if_infeasible(self.optimality_status, self.name)

        self.opt_fn_value = self.mod.objective.value()
        print('Objective function = %f' % self.opt_fn_value)

        print('Solve time = %.2f sec\n' % self.solver_time)

    def store_results(self):
        import sqlite3

        def setup_results_paths():
            self.paths['results'] = os.path.join(self.paths['outputs'], 'results')
            self.paths['LA_results_db'] = os.path.join(self.paths['results'], 'LA_results.db')
            self.paths['TR_results_db'] = \
                os.path.join(self.paths['results'], 'LA_trimmed_results.db')
            os.makedirs(self.paths['results'])

        def make_results_dfs():
            for name, dkvar in self.vars.items():
                dkvar.to_df()
                dkvar.remove_LA_int_from_results(self.sets['main_intervals'].indices)

        def write_LA_results():
            LA_connection = sqlite3.connect(self.paths['LA_results_db'])
            for name, dkvar in self.vars.items():
                dkvar.write_to_csv(self.paths['results'], removed_LA=False)
                dkvar.result_df.to_sql(name, LA_connection)
            LA_connection.close()
            print("Variables written as DB and CSV (with look ahead)")

        def write_TR_results():
            TR_connection = sqlite3.connect(self.paths['TR_results_db'])
            for name, dkvar in self.vars.items():
                dkvar.write_to_csv(self.paths['results'], removed_LA=True)
                dkvar.result_df_trimmed.to_sql(name, TR_connection)
            TR_connection.close()
            print("Variables written as DB and CSV (without look ahead)")

        setup_results_paths()
        make_results_dfs()

        if self.settings['WRITE_RESULTS_WITH_LOOK_AHEAD']:
            write_LA_results()

        if self.settings['WRITE_RESULTS_WITHOUT_LOOK_AHEAD']:
            write_TR_results()


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Missing path to input folder as an argument")
        exit()

    name = sys.argv[1]
    path_to_inputs = sys.argv[2]
    model = ucModel(name, path_to_inputs)
