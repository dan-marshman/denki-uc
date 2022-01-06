import denkiuc.uc_model as uc
import denkiuc.denki_paths
import os

dk_paths = denkiuc.denki_paths.dk_paths
path_to_test1 = os.path.join(dk_paths['denki_examples'], 'test1')
test_model = uc.ucModel('test1', path_to_test1)
test_model.prepare_model()
test_model.run_model()
