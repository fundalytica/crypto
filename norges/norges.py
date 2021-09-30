import sys
import difflib
from datetime import datetime

from colorama import Fore,Style
import pandas as pd
import numpy as np

from utils import utils, data
import iex.iex_symbols as iex_symbols

#pd.set_option('display.max_rows', None)

def sanitize(str):
    for s in ['.', ',', "'", '`', '-', '/', '(', ')', 'Co', 'Company', 'Corp', 'Class A']:
        str = str.replace(s, '')
    str = str.replace(' ', '')
    return str.upper()

def similarity(a,b):
    a = sanitize(a)
    b = sanitize(b)
    return difflib.SequenceMatcher(None, a, b).ratio()

def main():
    # norges xlsx
    year = 2018
    input_file = f'{utils.file_path(__file__)}/data/EQ_{year}_Country.xlsx'
    utils.cprint(f'\n[ Norges - Year {year} ]', Fore.CYAN)
    utils.cprint(input_file, Fore.YELLOW)
    df_norges = pd.read_excel(input_file, engine='openpyxl')
    utils.cprint(f'df_norges: {df_norges.shape}', Fore.GREEN)

    # norges us inc
    utils.cprint('\n[ Norges - Incorporation Country == USA ]', Fore.CYAN)
    us_inc = df_norges['Incorporation Country'] == 'United States'
    utils.cprint(f'df_norges[us_inc]: {df_norges[us_inc].shape}', Fore.GREEN)
    # utils.cprint('\n[ Incorporation Country == USA AND Country != USA ]', Fore.CYAN)
    # not_us_country = df_norges['Country'] != 'United States'
    # print(df_norges[us_inc & not_us_country])

    # out
    output_file = f'{utils.file_path(__file__)}/data/EQ_{year}.csv'
    try:
        # resume from output csv file
        utils.cprint(f'\n[ Existing Output File ]', Fore.CYAN)
        utils.cprint(output_file, Fore.YELLOW)
        df_out = pd.read_csv(output_file)
        # current progress
        count = len(df_out[df_out['Similarity'] == 1.0].index)
        utils.cprint(f'Match: {count}', Fore.YELLOW)
        count = len(df_out[df_out['Similarity'] < 1.0].index)
        utils.cprint(f'Similarity: {count}', Fore.YELLOW)
        count = len(df_out[np.isnan(df_out['Similarity'])].index)
        utils.cprint(f'Pending: {count}', Fore.YELLOW)
        total = len(df_out.index)
        print(f'Total: {total}\n')
    except Exception as e:
        utils.cprint(f'{e}', Fore.RED)
        # no output file, make new norges copy
        utils.cprint(f'\n[ Norges US Inc Copy ]', Fore.CYAN)
        df_out = df_norges[us_inc].copy()
    utils.cprint(f'df_out: {df_out.shape}', Fore.GREEN)

    # string similarity test
    # test_string = 'apples'
    # utils.cprint(f'\n[ Sequence Matcher Test - {test_string} ]', Fore.CYAN)
    # df_out = df_norges[us_inc].copy()
    # df_out['Similarity'] = df_norges.apply(lambda x: similarity(x['Name'], test_string), axis='columns')
    # df_out.sort_values(by='Similarity', ascending=False, inplace=True)
    # df_out = df_out[['Name','Similarity']]
    # print(df_out)

    # iex symbols
    utils.cprint(f'\n[ IEX - US Stock Symbols ]', Fore.CYAN)
    df_symbols = iex_symbols.symbols('us', sandbox=False)
    utils.cprint(f'df_symbols: {df_symbols.shape}', Fore.GREEN)
    # print(df_symbols)
    # print(df_symbols[df_symbols.index.str.startswith('GOOG')])
    # print(sanitize('Alphabet Inc - Class A'))
    # print(sanitize('Alphabet Inc'))

    def update_row(df, index, similarity, iex_name, iex_symbol):
        df.at[index, 'Similarity'] = similarity
        df.at[index, 'IEX Name'] = iex_name
        df.at[index, 'IEX Symbol'] = iex_symbol

    utils.cprint('\n[ Sequence Matcher ]', Fore.CYAN)

    for index,row in df_out.iterrows():
        if 'Similarity' in row:
            if not np.isnan(row["Similarity"]):
                if row["Similarity"] < 1.0:
                    # color = Fore.GREEN if row["Similarity"] == 1.0 else Fore.BLUE if row["Similarity"] >= 0.95 else Fore.RED
                    color = Fore.BLUE if row["Similarity"] >= 0.95 else Fore.RED
                    utils.cprint(f'⤴ pass {row["Name"]} - {row["IEX Name"]} - {row["Similarity"]:.3f} - {row["IEX Symbol"]}', color)
                continue

        match_name = row['Name']
        utils.cprint(f'\n> {match_name}', Fore.MAGENTA)

        column_name = 'name'
        matches = [symbol for symbol,row in df_symbols.iterrows() if sanitize(row[column_name]) == sanitize(match_name)]
        if len(matches):
            symbol = matches[0]
            symbol_name = df_symbols.loc[symbol][column_name]
            print(f'{Fore.YELLOW}✓ match{Style.RESET_ALL} {symbol_name} {Fore.GREEN}{symbol}{Style.RESET_ALL}')
            update_row(df_out, index, 1.0, symbol_name, symbol)
        else:
            current_similarity = 0.0
            current_symbol_name = None
            current_symbol = None

            # count symbols checked
            count = 1
            # time
            startTime = datetime.now()
            for symbol,row in df_symbols.iterrows():
                symbol_name = row[column_name]

                new_similarity = similarity(match_name, symbol_name)
                if(new_similarity > current_similarity):
                    print(f'{Fore.YELLOW}↑ similarity {new_similarity:,.2f}{Style.RESET_ALL} {symbol_name}')
                    current_similarity = new_similarity
                    current_symbol_name = symbol_name
                    current_symbol = symbol
                    # if current_similarity == 1.00:
                    #     break

                print(f'{(count / len(df_symbols.index) * 100):.3f}% - {count:,}/{len(df_symbols.index):,}', end='\r')
                count = count + 1
            update_row(df_out, index, current_similarity, current_symbol_name, current_symbol)
            # time
            time = datetime.now() - startTime
            utils.cprint(f'\n{time}', Fore.GREEN)

        #print(df_out.loc[index,:])
        #print(df_out.shape)
        # df_out.dropna(axis=0, how='any', inplace=True)
        df_out.to_csv(output_file, index=False)

if __name__ == '__main__':
    utils.handle_interrupt(main)