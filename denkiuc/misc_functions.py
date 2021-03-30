import logging
import os
import shutil
import sys


def set_logger_path(path_to_outputs):
    logger_path = os.path.join(path_to_outputs, 'warn.log')
    if 'unittest' not in sys.argv[0]:
        logging.basicConfig(filename=logger_path, level=logging.WARNING)


def make_folder(path_to_outputs):
    if os.path.exists(path_to_outputs):
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
        trace = data.traces['wind'][(scenario, 'Wind')].to_dict()
    elif technology == 'SolarPV':
        trace = data.traces['solarPV'][(scenario, 'Solar')].to_dict()
    else:
        print('Technology not known')
        exit()
    return trace
