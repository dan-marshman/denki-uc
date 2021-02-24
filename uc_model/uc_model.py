import pulp as pp
import os
import pandas as pd
import sys

module_path = os.path.dirname(__file__)
sys.path.append(module_path)


class ucModel():
    def __init__(self, name, inputs_path):
        print()
        print("-------------------------------------------------------------------------")
        print()

        self.name = name
        self.inputs_path = inputs_path

        print("Initiating UC model called", self.name)
        print("Using database folder located at   ", inputs_path)

        if not os.path.exists(self.inputs_path):
            print("Inputs path does not exist. Exiting")
            return

        self.INTERVALS_PER_HOUR = 2
        self.UNS_LOAD_PNTY = 10000
        self.UNS_RESERVE_PNTY = 10000
        self.UNS_INERTIA_PNTY = 10000
        print("Remember to define INTERVALS PER HOUR")

        self.load_parameters()
        self.create_sets()
        self.create_variables()
        self.build_model()
        self.solve_model()
        self.store_results()
        self.sanity_check_solution()

        print()
        print("---------------------------- Model generated ----------------------------")

    def load_parameters(self):
        import load_parameters as lp

        self = lp.load_settings(self)
        self = lp.load_traces(self)
        self = lp.load_unit_data(self)

    def create_sets(self):
        def assess_category(category):
            path_to_tech_categories_file = os.path.join(module_path, 'technology_categories.csv') 
            tech_categories_df = pd.read_csv(path_to_tech_categories_file, index_col=0)
            subset = []
            for u in self.sets['units']:
                unit_tech = self.unit_data['Technology'][u]
                if tech_categories_df[category][unit_tech] == 1:
                    subset.append(u)
            return subset

        self.sets = dict()

        self.sets['intervals'] = self.traces['demand'].index.to_list()
        self.sets['units'] = self.unit_data.index.to_list()

        self.sets['units_commit'] = assess_category('Commit')
        self.sets['units_storage'] = assess_category('Storage')
        self.sets['units_variable'] = assess_category('Variable')

    def create_variables(self):
        import variables as vr

        self.vars= dict()

        self.vars['commit_status'] = \
            vr.commitment_status(self.sets['intervals'], self.sets['units'])

        self.vars['energy_in_storage_MWh'] = \
            vr.energy_in_storage_MWh(self.sets['intervals'], self.sets['units_storage'])

        self.vars['inertia_MWsec'] = \
            vr.inertia(self.sets['intervals'], self.sets['units_commit'])

        self.vars['power_generated_MW'] = \
            vr.power_generated_MW(self.sets['intervals'], self.sets['units'])

        self.vars['reserve_MW'] = \
            vr.reserve_MW(self.sets['intervals'], self.sets['units'])

        self.vars['shut_down_status'] = \
            vr.shut_down_status(self.sets['intervals'], self.sets['units'])

        self.vars['start_up_status'] = \
            vr.start_up_status(self.sets['intervals'], self.sets['units'])

        self.vars['unserved_demand_MW'] = \
            vr.unserved_demand_MW(self.sets['intervals'])

        self.vars['unserved_inertia_MWsec'] = \
            vr.unserved_inertia_MWsec(self.sets['intervals'])

        self.vars['unserved_reserve_MW'] = \
            vr.unserved_reserve_MW(self.sets['intervals'])

        self.vars['charge_after_losses_MW'] = \
            vr.charge_after_losses_MW(self.sets['intervals'], self.sets['units_storage'])

    def build_model(self):
        import constraints as cnsts
        import obj_fn as obj

        self.mod = pp.LpProblem(self.name, sense=pp.LpMinimize)
        self.mod += obj.obj_fn(self)

        self = cnsts.create_constraints_df(self)
        self = cnsts.add_all_constraints_to_dataframe(self)

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
        import store_results_to_df as sr
        
        self.results = dict()
        self.results['commit_status'] = sr.commit_status_to_df(self)
        self.results['energy_price_$pMWh'] = sr.energy_price_to_df(self)
        self.results['charge_after_losses_MW'] = sr.charge_after_losses_to_df(self)
        self.results['charge_before_losses_MW'] = sr.charge_before_losses_to_df(self)
        self.results['power_generated_MW'] = sr.power_generated_to_df(self)
        self.results['unserved_demand_MW'] = sr.unserved_demand_to_df(self)
        self.results['energy_in_storage_MWh'] = sr.energy_in_storage_to_df(self)

    def sanity_check_solution(self):
        import sanity_check_solution as scs

        scs.check_power_lt_capacity(self)
        scs.total_gen_equals_demand(self)
        scs.check_energy_charged_lt_charge_capacity(self)
        scs.check_storage_continiuity(self)
        scs.check_stored_energy_lt_storage_capacity(self)
