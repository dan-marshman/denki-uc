import logging
import os
import shutil
import sys


def set_logger_path(path_to_outputs):
    logger_path = os.path.join(path_to_outputs, 'warn.log')
    if 'unittest' not in sys.argv[0]:
        logging.basicConfig(filename=logger_path, level=logging.WARNING)


def make_outputs_folder(path_to_outputs):
    if os.path.exists(path_to_outputs):
        shutil.rmtree(path_to_outputs)
    
    os.makedirs(path_to_outputs)
