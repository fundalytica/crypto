import json
import datetime, pytz

import argparse

from fundalytica_utils import utils, stock

from yahoo import Yahoo

def run():
    argparser = argparse.ArgumentParser(description='Yahoo Finance Quote')
    argparser.add_argument("-s", "--symbol", help="stock symbol", required=True)
    args = argparser.parse_args()

    symbol = args.symbol

    yahoo = Yahoo()
    info = yahoo.request_quote(symbol)

    price = info['currentPrice']

    previousClose = info['previousClose']

    nyc_datetime = datetime.datetime.now(pytz.timezone('US/Eastern'))
    # isUSMarketOpen = stock.isUSMarketOpen(nyc_datetime)

    ask = info['ask']
    isMarketOpen = (ask > 0)

    date_fmt = "%B %d, %Y"
    time_fmt = "%I:%M:%S %p"

    data = {}
    data["date"] = nyc_datetime.strftime(date_fmt)
    data["time"] = nyc_datetime.strftime(time_fmt)

    data["symbol"] = args.symbol

    # data["price"] = ask
    data["price"] = price

    # data["change"] = round((ask / previousClose) - 1, 5)
    data["change"] = round((price / previousClose) - 1, 5)

    data["market"] = "open" if isMarketOpen else "closed"

    print(json.dumps(data))

run()