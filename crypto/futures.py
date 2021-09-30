import requests
import json
import pprint
import argparse

from datetime import datetime, timezone
from dateutil import tz

from colorama import Fore

from fundalytica_utils import utils

class Futures:
    def __init__(self):
        self.url = 'https://futures.kraken.com/derivatives/api/v3'
        self.tickers()
        self.pairs = ['xbtusd','ethusd']

    def tickers(self):
        response = requests.get(f'{self.url}/tickers')
        tickers = json.loads(response.text)

        if tickers['result'] == 'success':
            self.tickers = tickers['tickers']

    def tickers_print(self):
        print()

        for pair in self.pairs:
            real_time_index = self.real_time_index(pair)
            utils.cprint(f'{pair.upper()} real time index', Fore.CYAN)
            index_last = real_time_index['last']
            utils.cprint("${:,.0f}".format(index_last), Fore.GREEN)
            print()

            utils.cprint(f'{pair.upper()} fixed futures', Fore.CYAN)
            # self.fixed_futures_print(pair, 'month')
            # self.fixed_futures_print(pair, 'quarter')
            self.fixed_futures_print(pair, 'semiannual')
            print()

    # PI_ -> Perpetual Inverse Futures
    def perpetual_futures(self, pair):
        for ticker in self.tickers:
            if ticker['symbol'] == f'pi_{pair}':
                return ticker

    # FI_ -> Inverse Futures
    def fixed_futures(self, pair, period):
        for ticker in self.tickers:
            if f'fi_{pair}' in ticker['symbol']:
                if ticker['tag'] == period:
                    return ticker

    def all_futures_symbols(self):
        pairs = {}
        # xbtusd, ethusd, etc ...
        for pair in self.pairs:
            pairs[pair] = self.futures_symbols(pair)
        return pairs

    def futures_symbols(self, pair):
        symbols = {}
        for ticker in self.tickers:
            if any(item in ticker['symbol'] for item in [f'pi_{pair}',f'fi_{pair}']):
                symbols[ticker['tag']] = ticker['symbol']
        return symbols

    def fixed_futures_print(self, pair, period):
        ff = self.fixed_futures(pair, period)

        if ff:
            index_last = self.real_time_index(pair)['last']

            mark = ff['markPrice']
            expiration = self.expiration(ff)
            delta = self.days_left(expiration)

            premium = (mark / index_last - 1) * 100
            annualized_premium = premium / utils.days_delta_fractional(delta) * 365

            utils.cprint(f'{period} ({ff["symbol"]})', Fore.WHITE)
            utils.cprint(f'{self.expiration_format(expiration)} ({self.days_left_format(delta)})', Fore.RED)
            utils.cprint(f'{"${:,.0f}".format(mark)} ({"${:,.0f}".format(index_last)} index)', Fore.GREEN)

            utils.cprint(f'{"{:.1f}".format(premium)}% ({"{:.1f}".format(annualized_premium)}% annualized)', Fore.YELLOW)

    # IN_ -> Real Time Index
    def real_time_index(self, pair):
        for ticker in self.tickers:
            if ticker['symbol'] == f'in_{pair}':
                return ticker

    # RR_ -> Reference Rate
    def reference_rate(self, pair):
        for ticker in self.tickers:
            if ticker['symbol'] == f'rr_{pair}':
                return ticker

    # Last Trading: 16:00 London time
    # Settlement Time: Within 15 minutes after Last Trading
    def expiration(self, ticker):
        expiration = ticker['symbol'][-6:]
        date = datetime.strptime(expiration + "16:00:00", '%y%m%d%H:%M:%S')
        # date = date.replace(tzinfo=timezone.utc)
        date = date.replace(tzinfo=tz.gettz('Europe/London'))
        return date

    def expiration_format(self, expiration):
        return expiration.strftime('%d %b \'%y')

    def days_left(self, expiration):
        now = datetime.now(timezone.utc)
        delta = expiration - now
        return delta

    def days_left_format(self, delta):
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds // 60) % 60
        return f'{delta.days}d {hours}h {minutes}m'

    def server_time(self):
            now = datetime.now(timezone.utc)
            # .isoformat()
            # now = now[:-9]+'Z'
            # now = now.replace('+00:00', 'Z')
            return f'Server Time: {now.strftime("%H:%M:%S")} UTC'

argparser = argparse.ArgumentParser(description='Crypto Futures')

argparser.add_argument("--summary", action='store_true', help="futures summary")

argparser.add_argument("-p", "--provider", help="data provider")
argparser.add_argument("--tickers", action='store_true', help="show tickers")
argparser.add_argument("--symbols", action='store_true', help="ticker symbols only")

args = argparser.parse_args()

futures = Futures()

if args.summary:
    futures.tickers_print()

if args.provider == 'kraken':
    data = {}

    # add provider info
    data['provider'] = args.provider

    # check that tickers are available
    if args.tickers:
        # all data
        if not args.symbols:
            data = futures.tickers
        # only ticker symbols
        else:
            data['pairs'] = futures.all_futures_symbols()

    print(json.dumps(data))
