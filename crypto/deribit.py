import requests
import json

from pprint import pprint
# from tabulate import tabulate
from datetime import datetime, timezone

from rich import print
from rich.table import Table

# from rich import pretty
# pretty.install()
from rich import inspect
from rich import box

from rich.progress import track

# for step in track(range(100)):
    # do_step(step)
    # sleep(2)

# my_list = ["foo", "bar"]
# inspect(my_list, methods=True)
# inspect(my_list)

# print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())

class Deribit:
    def __init__(self, subdomain):
        self.url = f'https://{subdomain}.deribit.com/api/v2/'
        self.index = {}
        self.instruments = {}
        self.order_book = {}

    def load_index(self, currency):
        print(f"[cyan]load_index - {currency}[/cyan]")
        url = f'{self.url}public/get_index_price?index_name={currency.lower()}_usd'
        response = requests.get(url)
        index = json.loads(response.text)
        index = index['result']['index_price']
        self.index[currency] = index

    def load_instruments(self, currency):
        print(f"[cyan]load_instruments - {currency}[/cyan]")
        url = f'{self.url}public/get_instruments?currency={currency}&kind=option'
        response = requests.get(url)
        instruments = json.loads(response.text)
        instruments = instruments['result']
        self.instruments[currency] = instruments

    def load_instrument_order_book(self, instrument_name):
        print(f"[cyan]load_instrument_order_book - {instrument_name}[/cyan]")
        url = f'{self.url}public/get_order_book?instrument_name={instrument_name}'
        response = requests.get(url)
        order_book = json.loads(response.text)
        order_book = order_book['result']
        self.order_book[instrument_name] = order_book

def days_remaining(timestamp):
    now = datetime.now(timezone.utc)
    now = datetime.fromtimestamp(now.timestamp())
    date = datetime.fromtimestamp(timestamp / 1000)
    date = date.replace(hour=8, minute=0, second=0, microsecond=0)  # expiration 08:00 UTC
    days = (date - now).days
    return days

def add_bid_ask(options):
    for option in options:
        instrument_name = option['instrument_name']
        deribit.load_instrument_order_book(instrument_name)
        order_book = deribit.order_book[instrument_name]
        option['bid'] = order_book['best_bid_price']
        option['ask'] = order_book['best_ask_price']
    return options

def add_spread_percentage(options):
    for option in options:
        if option['bid'] and option['ask']:
            spread_pct = (option['ask'] - option['bid']) / option['bid'] * 100
            option['spread_pct'] = spread_pct
            option['spread_pct'] = round(option['spread_pct'], 2)
        else:
            option['spread_pct'] = '-'
    return options

def add_covered_call_info(options, price = 0, size = 1):
    for option in options:
        if option['option_type'] == 'call' and not isinstance(option['spread_pct'], str) and option['spread_pct'] < 5:
            current_price = deribit.index[option['base_currency']]
            buy_price = price if price else current_price

            premium = (option['bid'] * current_price) * size
            assignment = (option['strike'] - buy_price) * size

            yld = option['bid'] * 100
            yld_assignment = (premium + assignment) / (buy_price * size) * 100

            option['premium'] = f"[cyan]${int(premium):,}[/cyan] [white]${int(premium + assignment):,}(A)[/white]"
            # option['premium_assignment'] = ''#f"${int(premium + assignment):,}"

            option['yield'] = f"[cyan]{int(yld)}%[/cyan] [white]{int(yld_assignment)}%(A)[/white]"
            option['yield_annualized'] = f"[cyan]{int(yld / option['days'] * 365)}%[/cyan] [white]{int(yld_assignment / option['days'] * 365)}%(A)[/white]"

            # option['yield_assignment'] = ''#f"{int(yld_assignment)}%"
            # option['yield_assignment_annualized'] = ''#f"{int(yld_assignment / option['days'] * 365)}%"
        else:
            # option['premium'] = option['premium_assignment'] = option['yield'] = option['yield_assignment'] = option['yield_annualized'] = option['yield_assignment_annualized'] = '-'
            option['premium'] = option['yield'] = option['yield_annualized'] = '-'
    return options

def add_days(list):
    for item in list:
        item['days'] = days_remaining(item['expiration_timestamp'])
    return list

def add_date(list):
    for item in list:
        timestamp = item['expiration_timestamp']
        date = datetime.fromtimestamp(timestamp / 1000)
        date = date.strftime('%d%b%y')
        date = date.upper()
        item['date'] = date
    return list

def simple_option_type(list):
    for item in list:
        item['option_type'] = item['option_type'][0].upper()
    return list

def color_instrument(list, currency):
    current_price = deribit.index[currency]
    offset = 5

    for item in list:
        p = float(item['instrument_name'].split('-')[2])
        if p > current_price * (1-offset/100) and p < current_price * (1+offset/100):
            item['instrument_name'] = f'[yellow]{item["instrument_name"]}[/yellow]'
    return list

def select_columns(order, rows):
    r = []
    for item in rows:
        item = {k: item[k] for k in order}
        r.append(item)
    return r

def remove_keys(keys, list):
    for key in keys:
        for item in list:
            del item[key]
    return list

def filter_options(options, type, minimum_days, strike_distance):
    options = [item for item in options if item['option_type'] == type]
    options = [item for item in options if days_remaining(item['expiration_timestamp']) >= minimum_days]
    # percentage
    options = [item for item in options if item['strike'] >= (1 - strike_distance / 100) * deribit.index[currency]]
    options = [item for item in options if item['strike'] <= (1 + strike_distance / 100) * deribit.index[currency]]
    return options

def print_options_table(options, currency, price = 0, size = 1):
    options = add_date(options)
    options = add_days(options)
    options = add_bid_ask(options)
    options = add_spread_percentage(options)
    options = add_covered_call_info(options, price, size)

    options = simple_option_type(options)
    options = color_instrument(options, currency)

    options = sorted(options, key=lambda k: (k['option_type'], k['expiration_timestamp'], k['strike']))

    # columns = ['instrument_name', 'days', 'premium', 'premium_assignment', 'yield', 'yield_assignment', 'yield_annualized', 'yield_assignment_annualized']
    columns = ['instrument_name', 'days', 'premium', 'yield', 'yield_annualized']
    options = select_columns(columns, options)

    print(f'[green][ {currency} - Options Chain ][/green]')

    # TABLE
    table = Table(box=box.MINIMAL_DOUBLE_HEAD)
    # TABLE COLUMNS
    keys = options[0].keys()
    for k in keys:
        if k == 'instrument_name':
            table.add_column(k, style="yellow")
        elif k == 'days':
            table.add_column(k, justify="right")
        else:
            table.add_column(k)
    # TABLE ROWS
    for o in options:
        v = list(o.values())
        for idx in range(len(v)):
            v[idx] = str(v[idx])
        table.add_row(*v)
    # TABLE OUTPUT
    print(table)
    # TABLE

    # print(tabulate(options, headers='keys'))

test = False
deribit = Deribit('test' if test else 'www')

import inquirer
questions = [
    inquirer.List('currency', message="Pick your coin", choices=['BTC', 'ETH', 'SOL'])
]
currency = inquirer.prompt(questions)['currency']

size = 1
minimum_days = 20
# minimum_days = 2
strike_distance_pct = 10
# strike_distance_pct = 2

price = 0

deribit.load_index(currency)
index = deribit.index[currency]
print(f'[green][ {currency} @ {index:,} ][/green]')

deribit.load_instruments(currency)
options = deribit.instruments[currency]
options = filter_options(options, 'call', minimum_days, strike_distance_pct)

print(f'[yellow][ Size : {size:,} ][/yellow]')
print(f'[yellow][ Minimum Days : {minimum_days:,} days ][/yellow]')
print(f'[yellow][ Strike Distance : -/+ {strike_distance_pct:,}% ][/yellow]')
if price:
    print(f'[yellow][ Price @ {price:,} ][/yellow]')

print_options_table(options, currency, price, size)

# place your 10K trade

# import argparse
# argparser = argparse.ArgumentParser(description='Crypto Futures')
# argparser.add_argument("--summary", action='store_true', help="futures summary")
# argparser.add_argument("-p", "--provider", help="data provider")
# argparser.add_argument("--tickers", action='store_true', help="show tickers")
# argparser.add_argument("--symbols", action='store_true', help="ticker symbols only")
# args = argparser.parse_args()
# if args.summary:
# if args.provider == 'kraken':