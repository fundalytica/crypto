import requests

from colorama import Fore as color
from colorama import init
init(autoreset=True)

from functools import reduce

assets = [
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/1',
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/2',
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/10003',
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/10004'
]

data = {}

def load():
    print()

    for asset in assets:
        url = f'https://api.opensea.io/api/v1/asset/{asset}'
        response = requests.request('GET', url)
        data[asset] = response.json()
        print(f'{color.CYAN}✓ ${asset}')

def last_sale(asset):
    return data[asset]['last_sale']

def last_sale_info(last_sale):
    total_price = int(last_sale['total_price'])
    decimals = int(last_sale['payment_token']['decimals'])
    price = total_price / 10 ** decimals

    symbol = last_sale['payment_token']['symbol']

    usd_price = float(last_sale['payment_token']['usd_price'])
    usd = price * usd_price

    return price, symbol, usd

def best_order(asset, side):
    # side 0 is offers (bids), side 1 is listings (asks)

    orders = data[asset]['orders']

    # only orders with quantity of 1
    orders = filter(lambda o: o['quantity'] == '1', orders)

    orders = filter(lambda o: o['side'] == side, orders)
    orders = sorted(orders, key=lambda k: float(k['current_price']), reverse=(side == 0))

    return orders[0] if len(orders) else None

def order_info(order):
    current_price = float(order['current_price'])
    decimals = int(order['payment_token_contract']['decimals'])
    price = current_price / 10 ** decimals
    symbol = order['payment_token_contract']['symbol']

    usd_price = float(order['payment_token_contract']['usd_price'])
    usd = price * usd_price

    username = order['maker']['user']['username']
    if username is None:
        address = (order['maker']['address'][2:8]).upper()
        username = address

    return price, symbol, usd, username

def print_order(order):
    price, symbol, usd, username = order_info(order)
    print(f"{price} {symbol} = {usd:,.0f} USD{color.BLUE} by {username}")

def last_sales_total(acc, asset):
    price, symbol, usd = last_sale_info(last_sale(asset))

    if symbol not in acc['symbols']:
        acc['symbols'].append(symbol)
    acc['total'] += price

    acc['usd'] += usd

    return acc

def lowest_listings_total(acc, asset):
    return order_accumulator(acc, asset, 1)

def highest_offers_total(acc, asset):
    return order_accumulator(acc, asset, 0)

def order_accumulator(acc, asset, side):
    price, symbol, usd, username = order_info(best_order(asset, side))

    if symbol not in acc['symbols']:
        acc['symbols'].append(symbol)

    acc['total'] += price

    acc['usd'] += usd

    return acc

def output():
    for asset in data:
        print()

        # info
        print(f"{color.GREEN}[ {data[asset]['name']} ]")
        print(f"{data[asset]['permalink']}")

        # last sale
        print(f"{color.CYAN}[ Last Sale ]")
        price, symbol, usd = last_sale_info(last_sale(asset))
        print(f'{price} {symbol} = {usd:,.0f} USD')

        # best ask
        print(f"{color.YELLOW}[ Lowest Listing ]")
        best = best_order(asset, 1)
        if(best):
            print_order(best)
        else:
            print('-')

        # best bid
        print(f"{color.YELLOW}[ Highest Offer ]")
        best = best_order(asset, 0)
        if(best):
            print_order(best)
        else:
            print('-')

    print()

    totals = [
        { 'description': 'Last Sales Total', 'method': last_sales_total },
        { 'description': 'Lowest Listings Total', 'method': lowest_listings_total },
        { 'description': 'Highest Offers Total', 'method': highest_offers_total },
    ]

    for t in totals:
        print(f"{color.GREEN}[ {t['description']} ]")
        total_info = reduce(t['method'], assets, { 'total': 0, 'symbols': [], 'usd': 0 })
        print(f"{total_info['total']:,.2f} {'/'.join(total_info['symbols'])} = {total_info['usd']:,.0f} USD")

    print()

load()
output()