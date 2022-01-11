import denkiuc.denki_paths
import denkiuc.load_data as ld
import denkiuc.misc_functions as mf
import denkiuc.variables as va
import os
import pulp as pp


def run_opt_problem(name, prob_path):
    prob = init_prob(name)

    prob['paths'] = init_paths(prob_path)
    prob['settings'] = ld.load_settings(prob['paths'])
    prob['paths'] = complete_paths(prob['paths'], prob['settings'], prob['name'])

    mf.make_folder(prob['paths']['outputs'])
    mf.set_logger_path(prob['paths']['outputs'])

    prob['data'] = ld.load_data(prob['paths'], prob['settings'])
    prob['sets'], prob['data'], prob['m_sets'] = \
        arrange_sets_and_data(prob['data'], prob['settings'], prob['paths'])

    prob['vars'] = add_variables(prob['m_sets'])

    prob['mod'] = build_model(prob)
    prob['stats'] = run_model(prob)

    return prob


def init_prob(name):
    prob = dict()
    prob['name'] = name

    return prob


def init_paths(prob_path):
    paths = denkiuc.denki_paths.dk_paths
    paths['inputs'] = prob_path
    paths['settings'] = os.path.join(paths['inputs'], 'settings.csv')
    return paths


def complete_paths(paths, settings, name):
    paths['outputs'] = os.path.join(settings['OUTPUTS_PATH'], name)
    paths['results'] = os.path.join(paths['outputs'], 'results')
    paths['final_state'] = os.path.join(paths['results'], 'final_state.db')
    paths['LA_results_db'] = os.path.join(paths['results'], 'LA_results.db')
    paths['TR_results_db'] = os.path.join(paths['results'], 'TR_results.db')
    paths['arma_out_dir'] = os.path.join(paths['inputs'], 'arma_traces')

    return paths


def arrange_sets_and_data(data, settings, paths):
    sets = ld.load_master_sets(data, settings)
    sets = ld.load_unit_subsets(data, sets, paths)
    sets = ld.add_reserve_subsets(sets)
    sets = ld.load_interval_subsets(settings, sets)
    m_sets = ld.make_multi_sets(sets)

    data['probability_of_scenario'] = ld.define_scenario_probability(sets['scenarios'])

    if not data['missing_values']['initial_state']:
        data = ld.validate_initial_state_data(data, sets)

    data = ld.add_default_values(data, sets)
    data = ld.replace_reserve_requirement_index(data)

    print("\nParameters and sets are ready")

    return sets, data, m_sets


def add_variables(m_sets):
    vars = dict()

    vars['power_generated'] = va.dkVar('power_generated', 'MW', m_sets['in_sc_un'])

    vars['num_committed'] = va.dkVar('num_committed', '#Units', m_sets['in_sc_unco'], 'I')
    vars['inertia_provided'] = va.dkVar('inertia_provided', 'MW.s', m_sets['in_sc_unco'])
    vars['is_committed'] = va.dkVar('is_committed', 'Binary', m_sets['in_sc_unco'], 'B')
    vars['num_shutting_down'] = va.dkVar('num_shutting_down', '#Units', m_sets['in_sc_unco'], 'I')
    vars['num_starting_up'] = va.dkVar('num_starting_up', '#Units', m_sets['in_sc_unco'], 'I')

    vars['reserve_enabled'] = va.dkVar('reserve_enabled', 'MW', m_sets['in_sc_un_re'])

    vars['charge_after_losses'] = va.dkVar('charge_after_losses', 'MW', m_sets['in_sc_unst'])
    vars['energy_in_reservoir'] = va.dkVar('energy_in_reservoir', 'MWh', m_sets['in_sc_unst'])

    vars['unserved_inertia'] = va.dkVar('unserved_inertia', 'MW.s', m_sets['in'])

    vars['unserved_power'] = va.dkVar('unserved_power', 'MW', m_sets['in_sc'])

    vars['unserved_reserve'] = va.dkVar('unserved_reserve', 'MW', m_sets['in_sc_re'])

    return vars


def build_model(prob):
    import denkiuc.constraints as cnts
    import denkiuc.obj_fn as obj

    prob['mod'] = pp.LpProblem(prob['name'], sense=pp.LpMinimize)
    prob['mod'] += obj.obj_fn(prob)

    cnts_df = cnts.create_cnts_df(prob['paths']['inputs'])
    prob['mod'] = cnts.add_all_constraints_to_dataframe(prob, cnts_df)

    return prob['mod']


def run_model(prob):
    from denkiuc.add_custom_results import add_final_state
    import sqlite3

    sets, data, vars, mod, paths, name = \
        mf.prob_unpacker(prob, ['sets', 'data', 'vars', 'mod', 'paths', 'name'])

    stats = solve_model(mod, name)
    store_results(prob)

    final_state = add_final_state(data, vars, sets, paths)

    connection = sqlite3.connect(paths['final_state'])
    for name, series in final_state.items():
        series.to_sql(name, connection)

    connection.close()
    print("Final state db written")

    return stats


def solve_model(mod, name):
    import time

    def print_stats(stats):
        print('Model status: %s' % stats['optimality_status'])
        print('Objective function = %f' % stats['obj_fn_value'])
        print('Solve time = %.2f sec\n' % stats['solver_time'])

    time_start_solve = time.perf_counter()
    print('Begin solving the model\nOptimising...')
    mod.solve(pp.PULP_CBC_CMD(timeLimit=5, threads=0, msg=0, gapRel=0.01))
    print("Finished optimising\n")
    time_end_solve = time.perf_counter()

    stats = dict()
    stats['solver_time'] = time_end_solve - time_start_solve
    stats['optimality_status'] = pp.LpStatus[mod.status]
    mf.exit_if_infeasible(stats['optimality_status'], name)
    stats['obj_fn_value'] = mod.objective.value()
    print_stats(stats)

    return stats


def store_results(prob):
    import sqlite3

    sets, settings, vars, paths = mf.prob_unpacker(prob, ['sets', 'settings', 'vars', 'paths'])

    def make_results_dfs(vars, sets):
        for name, dkvar in vars.items():
            dkvar.to_df()
            dkvar.remove_LA_int_from_results(sets['main_intervals'].indices)

    def write_LA_results(vars, paths):
        LA_connection = sqlite3.connect(paths['LA_results_db'])
        for name, dkvar in vars.items():
            dkvar.write_to_csv(paths['results'], removed_LA=False)
            dkvar.result_df.to_sql(name, LA_connection)
        LA_connection.close()
        print("Variables written as DB and CSV (with look ahead)")

    def write_TR_results(vars, paths):
        TR_connection = sqlite3.connect(paths['TR_results_db'])
        for name, dkvar in vars.items():
            dkvar.write_to_csv(paths['results'], removed_LA=True)
            dkvar.result_df_trimmed.to_sql(name, TR_connection)
        TR_connection.close()
        print("Variables written as DB and CSV (without look ahead)")

    os.makedirs(paths['results'])
    make_results_dfs(vars, sets)

    if settings['WRITE_RESULTS_WITH_LOOK_AHEAD']:
        write_LA_results(vars, paths)

    if settings['WRITE_RESULTS_WITHOUT_LOOK_AHEAD']:
        write_TR_results(vars, paths)
