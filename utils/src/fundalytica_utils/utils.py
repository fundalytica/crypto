import os
import sys
import json
import pprint
import pathlib
from distutils import util

import pandas as pd

from colorama import init,Style
init(autoreset=True)

from pympler import asizeof

from datetime import timedelta

# user confirmation prompt
def confirm(question, default='no'):
    if default is None:
        prompt = " [y/n] "
    elif default == 'yes':
        prompt = " [Y/n] "
    elif default == 'no':
        prompt = " [y/N] "
    else:
        raise ValueError(f"Unknown setting '{default}' for default.")

    while True:
        try:
            resp = input(question + prompt).strip().lower()
            if default is not None and resp == '':
                return default == 'yes'
            else:
                return util.strtobool(resp)
        except ValueError:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

# handle keyboard interrupt while running script
def handle_interrupt(method):
    try:
        method()
    except KeyboardInterrupt:
        print('\nBye :)\n')
        sys.exit(0)

# running from terminal
def terminal():
    return sys.stdin.isatty()

# __file__
def file_path(file):
    return pathlib.Path(file).parent.absolute()

# __file__
def file_name(file):
    return os.path.splitext(os.path.basename(file))[0]

# __file__
def file_extension(file):
    return os.path.splitext(os.path.basename(file))[1]

# obj pretty printing (converts into json)
def obj_print(obj):
    print(json.dumps(obj, indent=4, sort_keys=True))

# pretty print
def pretty_print(obj):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)

# color print
def cprint(text, color):
    print(f'{color}{text}')

# data size in mb
def mbsize(data):
    return f'{(asizeof.asizeof(data) / 1024 / 1024):.2f} MB'

# https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#from-timestamps-to-epoch
def pd_ts_to_unix_ts(pd_ts):
    return (pd_ts - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

# unique list
def unique(lst):
    return list(set(lst))

# fractional days delta
def days_delta_fractional(delta):
    return delta.total_seconds() / timedelta(days=1).total_seconds()