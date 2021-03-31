import denkiuc.uc_model as uc
import unittest


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
        self.assertEqual(test_model.path_to_inputs, path)


if __name__ == '__main__':
    unittest.main()
