import denkiuc.uc_model as uc
import os


def test_prob_name_is_set():
    name = 'test_problem_name'
    prob = uc.init_prob(name)
    assert prob['name'] == name


def test_inputs_path_is_set():
    prob_path = 'test_problem_path'
    paths = uc.init_paths(prob_path)
    assert paths['inputs'] == prob_path


def test_settings_path_is_set():
    prob_path = 'test_problem_path'
    paths = uc.init_paths(prob_path)
    assert paths['settings'] == os.path.join(prob_path, 'settings.csv')


def make_complete_paths_inputs():
    prob_path = 'test_problem_path'
    paths = uc.init_paths(prob_path)
    settings = {'OUTPUTS_PATH': 'test_outputs_path'}
    name = 'test_problem_name'
    paths = uc.complete_paths(paths, settings, name)
    return paths


def test_outputs_path_is_set():
    paths = make_complete_paths_inputs()
    assert  \
        paths['outputs']  \
        ==  \
        os.path.join('test_outputs_path', 'test_problem_name')


def test_results_path_is_set():
    paths = make_complete_paths_inputs()
    assert \
        paths['results']  \
        ==  \
        os.path.join('test_outputs_path', 'test_problem_name', 'results')


def test_final_state_path_is_set():
    paths = make_complete_paths_inputs()
    assert \
        paths['final_state'] \
        == \
        os.path.join('test_outputs_path', 'test_problem_name', 'results', 'final_state.db')


def test_LA_results_db_path_is_set():
    paths = make_complete_paths_inputs()
    assert \
        paths['LA_results_db'] \
        == \
        os.path.join('test_outputs_path', 'test_problem_name', 'results', 'LA_results.db')


def test_TR_results_db_path_is_set():
    paths = make_complete_paths_inputs()
    assert \
        paths['TR_results_db'] \
        == \
        os.path.join('test_outputs_path', 'test_problem_name', 'results', 'TR_results.db')
