import denkiuc.denki_paths
import denkiuc.load_data as ld
import denkiuc.misc_functions as mf
import denkiuc.uc_model as uc
import denkiuc.arma_generator as ag
from rich.console import Console
import os
import time


console = Console()


def run_series(name, prob_path):
    series = init_series(name)

    series['paths'] = init_paths(prob_path)
    series['settings'] = ld.load_settings(series['paths'])
    series['paths'] = complete_paths(series['paths'], series['settings'], series['name'])
    mf.make_folder(paths['outputs'])

    series['settings']['NUM_KEEP_INTERVALS'] = \
        series['settings']['INTERVALS_PER_DAY'] - series['settings']['LOOK_AHEAD_INTS']

    series['traces'] = load_traces(paths)
    series['settings']['NUM_DAYS'] = get_number_of_days(series['traces'], series['settings'])
    series['traces'] = trim_traces_to_integer_days(series['traces'], series['settings'])
    series['traces'] = add_last_look_ahead(series['traces'], series['settings'])
    series['traces'] = reset_trace_index_to_zero(series['traces'])

    series['days_summary'] = cycle_days(series)
    print_status_table(series['days_summary'])


def init_series(name):
    series = dict()
    series['name'] = name

    return series


def init_paths(prob_path):
    paths = denkiuc.denki_paths.dk_paths
    paths['inputs'] = prob_path
    paths['settings'] = os.path.join(paths['inputs'], 'settings.csv')
    return paths


def complete_paths(paths, settings, name):
    paths['outputs'] = os.path.join(settings['OUTPUTS_PATH'], name)

    return paths


def load_traces(paths):
    trace_locations = ag.load_trace_locations(paths['inputs'])
    traces = ag.load_deterministic_traces(trace_locations, paths['inputs'])

    return traces


def get_number_of_days(traces, settings):
    import math

    num_days = len(traces['demand']) / settings['NUM_KEEP_INTERVALS']
    num_days = math.floor(num_days)

    return num_days


def reset_trace_index_to_zero(traces):
    for trace_name, trace in traces.items():
        traces[trace_name].index = list(range(len(trace)))

    return traces


def trim_traces_to_integer_days(traces, settings):
    last_interval = settings['NUM_DAYS'] * settings['NUM_KEEP_INTERVALS']
    for trace_name, trace in traces.items():
        traces[trace_name] = trace.loc[0:last_interval]

    return traces


def add_last_look_ahead(traces, settings):
    for trace_name, trace in traces.items():
        for i in range(settings['LOOK_AHEAD_INTS']):
            new_row = dict()
            one_day_earlier_row = \
                trace.iloc[len(trace) - i - 1].name
            for col in trace.columns:
                new_row[col] = trace[col][one_day_earlier_row]
            trace = trace.append(new_row, ignore_index=True)
        traces[trace_name] = trace

    return traces


def cycle_days(series):
    import pandas as pd

    settings, traces = mf.prob_unpacker(series, ['settings', 'traces'])

    def get_days_intervals(d, num_keep_intervals, intervals_per_day):
        first_interval = settings['NUM_KEEP_INTERVALS'] * d
        last_interval = first_interval + settings['INTERVALS_PER_DAY']
        days_intervals = list(range(first_interval, last_interval))
        return days_intervals

    all_days = dict()
    all_days_folder = os.path.join(paths['inputs'], 'days')
    days_summary = pd.DataFrame(columns=['OptimalityStatus'])

    for d in range(settings['NUM_DAYS']):
        days_intervals = \
            get_days_intervals(d, settings['NUM_KEEP_INTERVALS'], settings['INTERVALS_PER_DAY'])

        days_traces = filter_days_traces(days_intervals, traces)

        day = denkiDay(d, days_traces, all_days_folder, paths['outputs'])
        day.solve_day()
        all_days['day' + str(d)] = day
        days_summary = days_summary.append(pd.Series(day.days_status, name=day.name))

    console.print("------------------------------------------------------")
    console.print("\nAll days have been run\n\n", style='bold')

    return days_summary


def filter_days_traces(days_intervals, traces):
    days_traces = dict()

    for trace_name, trace in traces.items():
        trace.index = trace.index.set_names(['Interval'])
        days_traces[trace_name] = trace.loc[days_intervals, :]

    return days_traces


def print_status_table(days_summary):
    from rich.table import Table

    all_days_table = Table(show_header=True, header_style='bold magenta')

    all_days_table.add_column('Day')
    for col in days_summary.columns:
        all_days_table.add_column(col)

    for index, row_vals in enumerate(days_summary.values.tolist()):
        row = [str(index)]
        row += [str(x) for x in row_vals]
        all_days_table.add_row(*row)

    console.print("Summary information", style='bold')
    console.print(all_days_table)


class denkiDay():
    def __init__(self, day_number, days_traces, all_days_folder, path_to_outputs):
        import denkiuc.misc_functions as mf
        import shutil

        self.time_start_day = time.perf_counter()

        console.print('---- Running day %d ----' % day_number, style="bold red")
        self.name = 'day' + str(day_number)
        self.all_days_folder = all_days_folder
        self.all_days_inputs_folder = os.path.dirname(all_days_folder)
        self.prev_day = 'day' + str(day_number - 1)
        self.input_path = os.path.join(self.all_days_folder, self.name)
        self.prev_day_outputs_folder = os.path.join(path_to_outputs, self.prev_day)

        mf.make_folder(self.input_path)

        files_in_folder = \
            [f for f in os.listdir(self.all_days_inputs_folder)
             if f[-4:] == '.csv' and f[:-4] not in days_traces.keys()]

        for f in files_in_folder:
            src_path = os.path.join(self.all_days_inputs_folder, f)
            dst_path = os.path.join(self.input_path, f)
            shutil.copyfile(src_path, dst_path)

        for trace_name, trace in days_traces.items():
            dst_path = os.path.join(self.input_path, trace_name+'.csv')
            trace.to_csv(dst_path)

        if os.path.exists(self.prev_day_outputs_folder):
            src_path = os.path.join(self.prev_day_outputs_folder, 'results', 'final_state.db')
            dst_path = os.path.join(self.input_path, 'initial_state.db')
            shutil.copyfile(src_path, dst_path)

    def solve_day(self):
        day_prob = uc.run_opt_problem(self.name, self.input_path)

        self.days_status = dict()
        self.days_status['OptimalityStatus'] = day_prob['stats']['optimality_status']
        self.days_status['ObjFnVal'] = day_prob['stats']['obj_fn_value']
        self.days_status['SolverTime'] = day_prob['stats']['solver_time']

        time_end_day = time.perf_counter()
        self.days_status['TotalRunTime'] = time_end_day - self.time_start_day

        print()


paths = denkiuc.denki_paths.dk_paths
path_to_test_series = os.path.join(paths['denki_examples'], 'test_series')
run_series('test_series', path_to_test_series)
# test_series = denkiSeries('test_series', path_to_test_series)
# test_series.cycle_days()
# test_series.print_status_table()
