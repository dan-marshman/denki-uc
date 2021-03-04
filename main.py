from denkiuc import uc_model as uc
import os

path_to_inputs = os.path.join(os.getcwd(), 'examples', 'test1')
test_model = uc.ucModel('test1', path_to_inputs)
