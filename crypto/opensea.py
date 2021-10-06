import requests


from colorama import Fore as color
from colorama import init
init(autoreset=True)

assets = [
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/1',
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/2',
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/10003',
    '0x10daa9f4c0f985430fde4959adb2c791ef2ccf83/10004',
]

def print_orders(orders):
    for order in orders:
        decimals = int(order['payment_token_contract']['decimals'])
        symbol = order['payment_token_contract']['symbol']
        current_price = float(order['current_price'])
        username = order['maker']['user']['username']
        print(f"{current_price / 10 ** decimals} {symbol}{color.BLUE} by {username}")

for asset in assets:
    url = f'https://api.opensea.io/api/v1/asset/{asset}'

    response = requests.request('GET', url)

    json = response.json()
    keys = json.keys()

    print()
    name = f"{color.GREEN}[ {json['name']} ]"
    symbol = json['last_sale']['payment_token']['symbol']
    decimals = int(json['last_sale']['payment_token']['decimals'])

    print(name)
    print(json['permalink'])
    # print(json['asset_contract']['schema_name'])

    print(f"{color.YELLOW}[ Last Sale ]")
    total_price = int(json['last_sale']['total_price'])
    print(f'{total_price / 10 ** decimals} {symbol}')

    # orders
    orders = json['orders']
    listings = filter(lambda o: o['side'] == 1, orders)
    listings = sorted(listings, key=lambda k: float(k['current_price']), reverse=False)
    offers = filter(lambda o: o['side'] == 0, orders)
    offers = sorted(offers, key=lambda k: float(k['current_price']), reverse=True)

    print(f"{color.YELLOW}[ Lowest Listing ]")
    if(len(listings)):
        print_orders(listings[:1])
    else:
        print('-')

    print(f"{color.YELLOW}[ Highest Offer ]")
    if(len(offers)):
        print_orders(offers[:1])
    else:
        print('-')

print()
