
from gc import collect
import os
import requests
from datetime import datetime
from functools import reduce
from dotenv import load_dotenv
from colorama import Fore as color
from colorama import init

init(autoreset=True)
load_dotenv()

assets = [
    # metakey
    # {'asset_contract_address': '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83', 'token_id': '1'},
    # {'asset_contract_address': '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83', 'token_id': '2'},
    # {'asset_contract_address': '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83',
    #     'token_id': '10003'},
    # {'asset_contract_address': '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83',
    #     'token_id': '10004'},
]

collections = [
    # rtfkt
    {'collection_slug': 'clonex'},
    {'collection_slug': 'rtfkt-mnlth'},
    {'collection_slug': 'cyber-factory-2'},
    {'collection_slug': 'rtfkt-podx'},
    {'collection_slug': 'mintdiscone'},
]

api_key = os.getenv('X-API-KEY')
headers = {'X-API-KEY': api_key}
assets_data = {}
collections_data = {}


def load_assets():
    for i in range(len(assets)):
        asset = assets[i]

        # https://docs.opensea.io/reference/retrieving-a-single-asset
        url = f"https://api.opensea.io/api/v1/asset/{asset['asset_contract_address']}/{asset['token_id']}?include_orders=true"

        response = requests.request("GET", url, headers=headers)
        assets_data[i] = response.json()
        print(f'{color.CYAN}✓ {url}')


def load_collections():
    for i in range(len(collections)):
        collection = collections[i]

        # https://docs.opensea.io/reference/retrieving-a-single-collection
        url = f"https://api.opensea.io/api/v1/collection/{collection['collection_slug']}"

        response = requests.request("GET", url, headers=headers)
        collections_data[i] = response.json()["collection"]
        print(f'{color.CYAN}✓ {url}')


def last_sale(asset):
    return assets_data[asset]['last_sale']


def last_sale_info(last_sale):
    total_price = int(last_sale['total_price'])
    decimals = int(last_sale['payment_token']['decimals'])
    price = total_price / 10 ** decimals

    symbol = last_sale['payment_token']['symbol']

    usd_price = float(last_sale['payment_token']['usd_price'])
    usd = price * usd_price

    ts = last_sale['event_timestamp']

    return price, symbol, usd, ts


def best_order(asset, side):
    # side 0 is offers (bids), side 1 is listings (asks)

    orders = assets_data[asset]['orders']

    if orders is None:
        return None

    # only orders with quantity of 1
    orders = filter(lambda o: o['quantity'] == '1', orders)

    orders = filter(lambda o: o['side'] == side, orders)
    orders = sorted(orders, key=lambda k: float(
        k['current_price']), reverse=(side == 0))

    return orders[0] if len(orders) else None


def order_info(order):
    current_price = float(order['current_price'])
    decimals = int(order['payment_token_contract']['decimals'])
    price = current_price / 10 ** decimals
    symbol = order['payment_token_contract']['symbol']

    usd_price = float(order['payment_token_contract']['usd_price'])
    usd = price * usd_price

    # print(order['maker'])
    # username = order['maker']['user']['username']
    # if username is None:
    #     username = address

    # address = (order['maker']['address'][2:8]).upper()
    address = (order['maker']['address'])

    return price, symbol, usd, address


def print_order(order):
    # price, symbol, usd, username = order_info(order)
    # print(f"{price} {symbol} = {usd:,.0f} USD{color.BLUE} by {username}")
    price, symbol, usd, address = order_info(order)
    print(f"{price} {symbol} = {usd:,.0f} USD{color.BLUE} by {address}")


def last_sales_total(acc, asset):
    price, symbol, usd, ts = last_sale_info(last_sale(asset))

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


def output_assets():
    for i in range(len(assets_data)):
        print()

        # info
        print(f"{color.GREEN}[ {assets_data[i]['name']} ]")
        print(f"{assets_data[i]['permalink']}")

        # last sale
        price, symbol, usd, ts = last_sale_info(last_sale(i))
        now = datetime.now()
        ts = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')  # 2022-04-05T08:31:24
        delta = now - ts
        print(f"{color.CYAN}[ Last Sale - {delta.days}d ]")

        print(f'{price} {symbol} = {usd:,.0f} USD')

        # best ask
        print(f"{color.YELLOW}[ Lowest Listing ]")
        best = best_order(i, 1)
        if(best):
            print_order(best)
        else:
            print('-')

        # best bid
        print(f"{color.YELLOW}[ Highest Offer ]")
        best = best_order(i, 0)
        if(best):
            print_order(best)
        else:
            print('-')

    print()

    totals = [
        {'description': 'Last Sales Total', 'method': last_sales_total},
        {'description': 'Lowest Listings Total', 'method': lowest_listings_total},
        {'description': 'Highest Offers Total', 'method': highest_offers_total},
    ]

    print_totals(totals, assets_data)

    print()


def print_totals(totals, data):
    for t in totals:
        print(f"{color.MAGENTA}[ {t['description']} ]")
        total_info = reduce(t['method'], range(len(data)), {
                            'total': 0, 'symbols': [], 'usd': 0})
        print(
            f"{total_info['total']:,.2f} {'/'.join(total_info['symbols'])} = {total_info['usd']:,.0f} USD")


def floor_info(collection):
    price = collection['stats']['floor_price']
    payment_token = collection['payment_tokens'][0]

    symbol = payment_token['symbol']
    usd_price = payment_token['usd_price']
    usd = price * usd_price

    return price, symbol, usd


def floor_total(acc, collection_index):
    price, symbol, usd = floor_info(collections_data[collection_index])

    if symbol not in acc['symbols']:
        acc['symbols'].append(symbol)
    acc['total'] += price

    acc['usd'] += usd

    return acc


def output_collections():
    for i in range(len(collections_data)):
        c = collections_data[i]

        print()

        # info
        print(f"{color.GREEN}[ {c['name']} ]")

        urls = f"https://opensea.io/collection/{c['slug']}"
        if c['external_url'] is not None:
            urls += ' | ' + f"{c['external_url']}"
        # if c['discord_url'] is not None:
        #     urls += ' | ' + f"{c['discord_url']}"
        print(urls)

        # floor
        price, symbol, usd = floor_info(c)
        print(f"{color.CYAN}[ Floor ]")
        print(f'{price} {symbol} = {usd:,.0f} USD')

    print()

    totals = [
        {'description': 'Floor Total', 'method': floor_total},
    ]
    print_totals(totals, collections_data)

    print()


load_assets()
if(len(assets)):
    output_assets()

load_collections()
if(len(collections)):
    output_collections()
