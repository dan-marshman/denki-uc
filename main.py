from uc_model import uc_model as uc
import os


path_to_inputs = \
    os.path.abspath(os.path.join(os.sep, 'Users', 'danie', 'Documents', 'denki-uc', 'input_dbs', 'test1'))

test_model = uc.ucModel('test1', path_to_inputs)

