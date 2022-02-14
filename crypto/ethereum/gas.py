import json

import requests

import pprint
pp = pprint.PrettyPrinter(indent=2, compact=True)

from colorama import Fore, Style

from keys import alchemy as key

url = f'https://eth-mainnet.alchemyapi.io/v2/{key}'
method = 'eth_gasPrice'

dict = {
    "jsonrpc":  "2.0",
    "method":   method,
    "params":   [],
    "id":       "1"
}

print(f'{Fore.MAGENTA}alchemy.com{Style.RESET_ALL}')
# print(f'{Fore.CYAN}{url}{Style.RESET_ALL}')
print(f'{Fore.CYAN}{method}{Style.RESET_ALL}')

res = requests.post(url, json=dict)
res = res.json()

print(Fore.GREEN, end='')
pp.pprint(res)
print(Style.RESET_ALL, end='')

gwei = res['result']

gwei = int(gwei, 16)
print(f'{int(gwei / 1000000000)} gwei ({gwei})')