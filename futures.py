import requests
import json
import pprint

from datetime import datetime, timezone
from dateutil import tz

from colorama import Fore

from utils import utils

class Futures:
    def __init__(self):
        self.url = 'https://futures.kraken.com/derivatives/api/v3'
        self.tickers()

    def tickers(self):
        response = requests.get(f'{self.url}/tickers')
        tickers = json.loads(response.text)

        if tickers['result'] == 'success':
            self.tickers = tickers['tickers']

    def tickers_print(self):
        print()

        pairs = ['xbtusd','ethusd']

        for pair in pairs:
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

    def fixed_futures_symbols(self, pair):
        symbols = {}
        for ticker in self.tickers:
            if f'fi_{pair}' in ticker['symbol']:
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
            annualized_premium = premium / delta.days * 365

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

a = Futures()

print(a.fixed_futures_symbols('xbtusd'))
print(a.fixed_futures_symbols('ethusd'))