import denkiuc.uc_model as uc
import os

path_to_test1= os.path.join(uc.path_to_examples, 'test1')
test_model = uc.ucModel('test1', path_to_test1)
test_model.solve()

