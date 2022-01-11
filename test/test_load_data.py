# import denkiuc.uc_model as uc
# import denkiuc
# import os
# import unittest


# test1_path = os.path.join(uc.path_to_tests, 'test1')


# class load_dataTests(unittest.TestCase):
    # def test_traces_are_loaded(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # val = test_model.data.traces['demand'][(0, 'Demand')][0]
        # self.assertEqual(val, 1000)

    # def test_unit_data_is_loaded(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # val = test_model.data.units['Capacity_MW']['Coal1']
        # self.assertEqual(val, 510)

    # def test_initial_state_is_loaded(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # val = test_model.data.initial_state['PowerGeneration_MW']['Coal1']
        # self.assertEqual(val, 300)

    # def test_initial_state_commit_is_wrong_1(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # test_model.data.initial_state['NumCommited']['Coal1'] = 1.8
        # test_model.data.validate_initial_state_data(test_model.sets)
        # result = test_model.data.initial_state['NumCommited']['Coal1']
        # self.assertEqual(result, 1)

    # def test_initial_state_commit_is_wrong_2(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # test_model.data.initial_state['NumCommited']['Coal1'] = -0.3
        # test_model.data.validate_initial_state_data(test_model.sets)
        # result = test_model.data.initial_state['NumCommited']['Coal1']
        # self.assertEqual(result, 0)

    # def test_initial_state_commit_is_wrong_3(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # test_model.data.initial_state['NumCommited']['Coal1'] = 0.3
        # test_model.data.validate_initial_state_data(test_model.sets)
        # result = test_model.data.initial_state['NumCommited']['Coal1']
        # self.assertEqual(result, 0)

    # def test_arma_demand(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # scenarios = test_model.sets['scenarios']
        # scenarios.indices = list(range(5))
        # test_model.data.add_arma_scenarios(scenarios, random_seed=12)
        # result = \
            # (
             # round(test_model.data.traces['demand'][(3, 'Demand')][12], 3),
             # round(test_model.data.traces['wind'][(2, 'Wind')][21], 3),
             # round(test_model.data.traces['solarPV'][(1, 'Solar')][37], 3),
            # )
        # self.assertEqual(result, (2393.924, 0.442, 0))

    # def test_negative_trace(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # scenarios = test_model.sets['scenarios']
        # scenarios.indices = list(range(2))

        # test_model.data.orig_traces['demand']['Demand'][12] = -5000
        # test_model.data.orig_traces['wind']['Wind'][12] = -5000
        # test_model.data.orig_traces['solarPV']['Solar'][12] = -5000

        # test_model.data.add_arma_scenarios(scenarios, random_seed=5)

        # result = (
                  # test_model.data.traces['demand'][(1, 'Demand')][12],
                  # test_model.data.traces['wind'][(1, 'Wind')][12],
                  # test_model.data.traces['solarPV'][(1, 'Solar')][12]
                # )

        # self.assertEqual(result, (0, 0, 0))

    # def test_too_large_intermittent_trace(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # scenarios = test_model.sets['scenarios']
        # scenarios.indices = list(range(2))

        # test_model.data.orig_traces['wind']['Wind'][12] = 5000
        # test_model.data.orig_traces['solarPV']['Solar'][12] = 5000
        # test_model.data.orig_traces['demand']['Demand'][12] = 5000

        # test_model.data.add_arma_scenarios(scenarios, random_seed=5)

        # result = (
                  # round(test_model.data.traces['demand'][(1, 'Demand')][12]),
                  # test_model.data.traces['wind'][(1, 'Wind')][12],
                  # test_model.data.traces['solarPV'][(1, 'Solar')][12]
                # )
        # self.assertEqual(result, (4821, 1, 1))


# class settingsTests(unittest.TestCase):
    # def test_settings_loaded(self):
        # test_model = uc.ucModel('test1', test1_path)
        # val = test_model.settings['OUTPUTS_PATH']

        # expected_path = os.path.abspath(os.path.join(os.sep,
                                                     # 'Users',
                                                     # 'danie',
                                                     # 'Documents',
                                                     # 'denki-uc',
                                                     # 'test',
                                                     # 'outputs'))

        # self.assertEqual(val, expected_path)


# class setsTests(unittest.TestCase):
    # def test_set_name(self):
        # master_set = denkiuc.load_data.dkSet('master', [1, 2, 3, 4])
        # self.assertEqual(master_set.name, 'master')

    # def test_sets_intervals(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()

        # result = test_model.sets['intervals'].indices
        # expected_set = list(range(48))
        # self.assertEqual(result, expected_set)

    # def test_sets_commit(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # result = test_model.sets['units_commit'].indices
        # expected_set = ['Coal1', 'Coal2', 'Gas1', 'Gas2']
        # self.assertEqual(result, expected_set)

    # def test_sets_variable(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # result = test_model.sets['units_variable'].indices
        # expected_set = ['SolarPV1', 'Wind1']
        # self.assertEqual(result, expected_set)

    # def test_sets_storage(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # result = test_model.sets['units_storage'].indices
        # expected_set = ['Battery1']
        # self.assertEqual(result, expected_set)

    # def test_validate_subset_pass(self):
        # master_set = denkiuc.load_data.dkSet('master', [1, 2, 3, 4])
        # sub_set = denkiuc.load_data.dkSet('sub', [1, 2])
        # validate_result = sub_set.validate_set(master_set)
        # self.assertEqual(validate_result, None)

    # def test_validate_subset_fail(self):
        # master_set = denkiuc.load_data.dkSet('master', [1, 2, 3, 4])
        # sub_set = denkiuc.load_data.dkSet('sub', [1, 2, 'NonMember'])
        # with self.assertRaises(ValueError) as error:
            # sub_set.validate_set(master_set)
        # self.assertEqual(str(error.exception), 'Subset validation error')

    # def test_look_ahead_intervals_correct(self):
        # test_model = uc.ucModel('test1', test1_path)
        # test_model.arrange_data()
        # actual_result = test_model.sets['look_ahead_intervals'].indices
        # expected_set = list(range(28, 48))
        # self.assertEqual(expected_set, actual_result)


# if __name__ == '__main__':
    # unittest.main()
