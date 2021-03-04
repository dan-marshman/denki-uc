import os
import uc_model as uc
import unittest


path_to_denki = os.path.join(os.sep, 'Users', 'danie', 'Documents', 'denki-uc')
path_to_inputs = os.path.abspath(os.path.join(path_to_denki, 'input_dbs', 'test1'))


class initTests(unittest.TestCase):
    def test_name_is_set(self):
        name = 'hello'
        path = 'goodbye'

        test_model = uc.ucModel(name, path)
        self.assertEqual(test_model.name, name)

    def test_inputs_path_is_set(self):
        name = 'hello'
        path = 'goodbye'

        test_model = uc.ucModel(name, path)
        self.assertEqual(test_model.inputs_path, path)


class traceTests(unittest.TestCase):
    def test_traces_are_loaded(self):
        test_model = uc.ucModel('test1', path_to_inputs)
        val = test_model.traces['demand']['VIC'][0] 
        self.assertEqual(val, 1000)


class settingsTests(unittest.TestCase):
    def test_settings_loaded(self):
        test_model = uc.ucModel('test1', path_to_inputs)
        val = test_model.settings['OUTPUTS_PATH']
        expected_path = \
            os.path.abspath(os.path.join(os.sep, 'Users', 'danie', 'Documents', 'denki-uc', 'outputs'))
        self.assertEqual(val, expected_path)


class setsTests(unittest.TestCase):
    def test_sets_intervals(self):
        test_model = uc.ucModel('test1', path_to_inputs)

        val = test_model.sets['intervals']
        expected_set = list(range(48))
        self.assertEqual(val, expected_set)


    def test_sets_commit(self):
        test_model = uc.ucModel('test1', path_to_inputs)
        val = test_model.sets['units_commit']
        expected_set = ['Coal1', 'Coal2', 'Gas1', 'Gas2']
        self.assertEqual(val, expected_set)

    def test_sets_variable(self):
        test_model = uc.ucModel('test1', path_to_inputs)
        val = test_model.sets['units_variable']
        expected_set = ['SolarPV1', 'Wind1']
        self.assertEqual(val, expected_set)

    def test_sets_storage(self):
        test_model = uc.ucModel('test1', path_to_inputs)
        val = test_model.sets['units_storage']
        expected_set = ['Battery1']
        self.assertEqual(val, expected_set)


unittest.main()
