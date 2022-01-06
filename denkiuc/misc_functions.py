import logging
import os
import shutil
import sys
import pandas as pd

module_path = os.path.split(os.path.abspath(__file__))[0]
default_files_path = os.path.join(module_path, 'default_files')


def set_logger_path(path_to_outputs):
    logger_path = os.path.join(path_to_outputs, 'warn.log')
    if 'unittest' not in sys.argv[0]:
        logging.basicConfig(filename=logger_path, level=logging.WARNING)


def make_folder(path_to_outputs, keep_existing=False):
    if os.path.exists(path_to_outputs):
        if keep_existing is True:
            return
        else:
            shutil.rmtree(path_to_outputs)
    os.makedirs(path_to_outputs)


def get_max_reserves_per_unit(unit, reserve, unit_data):
    if reserve in ['PrimaryRaise', 'PrimaryLower']:
        max_reserves_per_unit = \
            unit_data['PrimaryReserves_pct'][unit] * unit_data['Capacity_MW'][unit]

    if reserve in ['SecondaryRaise', 'SecondaryLower']:
        max_reserves_per_unit = \
            unit_data['SecondaryReserves_pct'][unit] * unit_data['Capacity_MW'][unit]

    if reserve in ['TertiaryRaise', 'TertiaryLower']:
        max_reserves_per_unit = \
            unit_data['TertiaryReserves_pct'][unit] * unit_data['Capacity_MW'][unit]

    return max_reserves_per_unit


def get_resource_trace(scenario, region, technology, data):
    if technology == 'Wind':
        trace = data.traces['wind'][scenario].to_dict()
    elif technology == 'SolarPV':
        trace = data.traces['solarPV'][scenario].to_dict()
    else:
        print('Technology not known')
        exit()
    return trace


def print_preamble(name, path_to_inputs):
    print()
    print("-------------------------------------------------------------------------")
    print()
    print("Initiating UC model called", name)
    print("Using database folder located at  ", path_to_inputs)


def check_input_dir_exists(path_to_inputs):
    if not os.path.exists(path_to_inputs):
        print("Inputs path does not exist. Exiting")
        return


def exit_if_infeasible(status, name):
    if status == 'Infeasible':
        print("\n", name, 'was infeasible. Exiting.')


def load_default_file(filename):
    file_path = os.path.join(default_files_path, filename)
    data = pd.read_csv(file_path, index_col=0)
    return data
