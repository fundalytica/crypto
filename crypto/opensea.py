import requests

import pprint
pp = pprint.PrettyPrinter(indent=4)

asset = '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/1/'

url = f"https://api.opensea.io/api/v1/asset/{asset}"

response = requests.request("GET", url)

json = response.json()
keys = json.keys()

# pp.pprint(json)

# print(json['last_sale'])
# print(json['last_sale']['total_price'])

print()
name = json['name']
symbol = json['last_sale']['payment_token']['symbol']
decimals = int(json['last_sale']['payment_token']['decimals'])

print(name)
print(json['permalink'])
print(json['asset_contract']['schema_name'])

total_price = int(json['last_sale']['total_price'])
print('\n[ Last Sale ]')
print(f'{total_price / 10 ** decimals} {symbol}')

# print('\nOrders')
orders = json['orders']
orders = sorted(orders, key=lambda k: float(k['current_price']), reverse=False)
offers = filter(lambda o: o['side'] == 0, orders)
listings = filter(lambda o: o['side'] == 1, orders)

def print_orders(orders):
    for order in orders:
        decimals = int(order['payment_token_contract']['decimals'])
        symbol = order['payment_token_contract']['symbol']
        current_price = float(order['current_price'])
        print(f"{order['maker']['user']['username']} - {current_price / 10 ** decimals} {symbol}")

print('\n[ Listings ]')
print_orders(listings)
print('\n[ Offers ]')
print_orders(offers)
