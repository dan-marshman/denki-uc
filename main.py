import denkiuc.uc_model as uc
import os

path_to_test1= os.path.join(uc.path_to_denki_examples, 'test1')
print(path_to_test1)
test_model = uc.ucModel('test1', path_to_test1)
