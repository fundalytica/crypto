import json

import argparse
from yahoo import Yahoo

from utils import utils, data

def run():
    argparser = argparse.ArgumentParser(description='Yahoo Finance Historical Data')
    argparser.add_argument("-s", "--symbol", help="stock symbol", required=True)
    argparser.add_argument("--save", action='store_true', help="save data")

    args = argparser.parse_args()
    symbol = args.symbol

    yahoo = Yahoo()
    df = yahoo.request_historical_data(symbol, 'max')

    json = df.to_json(orient='index')
    print(json)

    if args.save:
        path = utils.file_path(__file__)
        name = utils.file_name(__file__)

        csv = True
        extension = f'.{"csv" if csv else "pkl"}'

        file = f'{path}/{name}/{symbol}{extension}'
        data.df_write(df, file, verbose=True)

run()