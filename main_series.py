import denkiuc.denki_paths
import denkiuc.load_data as ld
import denkiuc.misc_functions as mf
import denkiuc.uc_model as uc
import denkiuc.arma_generator as ag
import os
import time


class denkiSeries():
    def __init__(self, name, path_to_inputs):
        self.name = name
        self.paths = denkiuc.denki_paths.dk_paths
        self.paths['inputs'] = path_to_inputs
        self.paths['settings'] = os.path.join(self.paths['inputs'], 'settings.csv')
        self.setup()

    def setup(self):
        self.settings = ld.load_settings(self.paths)
        self.paths['outputs'] = self.settings['OUTPUTS_PATH']
        mf.make_folder(self.paths['outputs'])

        self.settings['NUM_KEEP_INTERVALS'] = \
            self.settings['INTERVALS_PER_DAY'] - self.settings['LOOK_AHEAD_INTS']

        self.load_traces()
        self.get_number_of_days()
        self.trim_traces_to_integer_days()
        self.add_last_look_ahead()
        self.reset_trace_index_to_zero()

    def load_traces(self):
        trace_locations = ag.load_trace_locations(self.paths['inputs'])
        self.traces = ag.load_deterministic_traces(trace_locations, self.paths['inputs'])

    def get_number_of_days(self):
        import math

        self.num_days = len(self.traces['demand']) / self.settings['NUM_KEEP_INTERVALS']
        self.num_days = math.floor(self.num_days)

    def reset_trace_index_to_zero(self):
        for trace_name, trace in self.traces.items():
            self.traces[trace_name].index = list(range(len(trace)))

    def trim_traces_to_integer_days(self):
        last_interval = self.num_days * self.settings['NUM_KEEP_INTERVALS']
        for trace_name, trace in self.traces.items():
            self.traces[trace_name] = trace.loc[0:last_interval]

    def add_last_look_ahead(self):
        for trace_name, trace in self.traces.items():
            for i in range(self.settings['LOOK_AHEAD_INTS']):
                new_row = dict()
                one_day_earlier_row = \
                    trace.iloc[len(trace) - i - 1].name
                for col in trace.columns:
                    new_row[col] = trace[col][one_day_earlier_row]
                trace = trace.append(new_row, ignore_index=True)
            self.traces[trace_name] = trace

    def cycle_days(self):
        import pandas as pd

        all_days = dict()
        all_days_folder = os.path.join(self.paths['inputs'], 'days')
        all_days_status = pd.DataFrame(columns=['OptimalityStatus'])

        for d in range(self.num_days):
            first_interval = self.settings['NUM_KEEP_INTERVALS'] * d
            last_interval = first_interval + self.settings['INTERVALS_PER_DAY']
            days_intervals = list(range(first_interval, last_interval))
            days_traces = self.filter_days_traces(days_intervals)
            day = denkiDay(d, days_traces, all_days_folder, self.paths['outputs'])
            day.solve_day()
            all_days['day' + str(d)] = day
            all_days_status = all_days_status.append(pd.Series(day.days_status, name=day.name))

        print(all_days_status)

    def filter_days_traces(self, days_intervals):
        days_traces = dict()
        for trace_name, trace in self.traces.items():
            trace.index = trace.index.set_names(['Interval'])
            days_traces[trace_name] = trace.loc[days_intervals, :]
        return days_traces


class denkiDay():
    def __init__(self, day_number, days_traces, all_days_folder, path_to_outputs):
        import denkiuc.misc_functions as mf
        import shutil

        self.time_start_day = time.perf_counter()

        print('---- Running day ----', day_number)
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
            src_path = os.path.join(self.prev_day_outputs_folder, 'results', 'final_state.csv')
            dst_path = os.path.join(self.input_path, 'initial_state.csv')
            shutil.copyfile(src_path, dst_path)

    def solve_day(self):
        day_model = uc.ucModel(self.name, self.input_path)
        day_model.prepare_model()
        day_model.run_model()

        self.days_status = dict()
        self.days_status['OptimalityStatus'] = day_model.optimality_status
        self.days_status['ObjFnVal'] = day_model.opt_fn_value
        self.days_status['SolverTime'] = day_model.solver_time

        time_end_day = time.perf_counter()
        self.days_status['TotalRunTime'] = time_end_day - self.time_start_day


paths = denkiuc.denki_paths.dk_paths
path_to_test_series = os.path.join(paths['denki_examples'], 'test_series')
test_series = denkiSeries('test_series', path_to_test_series)
test_series.cycle_days()
