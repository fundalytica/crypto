# import csv

from . import utils

from colorama import Fore

import pandas as pd

import os

# def read_csv(file):
#     rows = []

#     with open(file, encoding='utf-8-sig') as csvfile:
#         for row in csv.reader(csvfile):
#             rows.append(row)

#     return rows

# read data frame
def df_read(file, index=None, sort=False, verbose=False):
    csv = utils.file_extension(file) == '.csv'

    if verbose:
        utils.cprint('\n[ DataFrame Read ]', Fore.GREEN)
        utils.cprint(file, Fore.CYAN)

    try:
        if csv:
            df = pd.read_csv(file, index_col=index)
        else:
            df = pd.read_pickle(file)

        if sort:
            df.sort_index(inplace=True)
        if verbose:
            print(f'\n{df}')
    except IOError as e:
        if verbose:
            utils.cprint('> File Not Found', Fore.RED)
        return None
    except pd.errors.EmptyDataError as e:
        if verbose:
            utils.cprint('> Empty Data', Fore.RED)
        return None

    return df

# write data frame
def df_write(df, file, index=True, sort=False, verbose=False):
    csv = utils.file_extension(file) == '.csv'

    dir = utils.file_path(file)
    if not os.path.exists(dir):
        os.mkdir(dir)

    if verbose:
        utils.cprint('\n[ DataFrame Write ]', Fore.GREEN)
        utils.cprint(file, Fore.CYAN)

    if sort:
        df.sort_index(inplace=True)

    if csv:
        df.to_csv(file, index=index)
    else:
        df.to_pickle(file, index=index)

    if verbose:
        utils.cprint('> OK', Fore.MAGENTA)