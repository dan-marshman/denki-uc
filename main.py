import denkiuc.uc_model as uc
import denkiuc.denki_paths
import os

dk_paths = denkiuc.denki_paths.dk_paths
path_to_test1 = os.path.join(dk_paths['denki_examples'], 'test1')
uc.run_opt_problem(name='test1', prob_path=path_to_test1)



