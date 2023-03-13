import requests
import json

from rich import print

class Deribit:
    def __init__(self, subdomain):
        self.url = f'https://{subdomain}.deribit.com/api/v2/'
        self.index = {}

    def load_index(self, currency):
        print(f"[cyan]load_index - {currency}[/cyan]")
        url = f'{self.url}public/get_index_price?index_name={currency.lower()}_usd'
        response = requests.get(url)
        index = json.loads(response.text)
        index = index['result']['index_price']
        self.index[currency] = index

test = False
deribit = Deribit('test' if test else 'www')

currencies = ["BTC", "ETH"]
for currency in currencies:
    deribit.load_index(currency)
    index = deribit.index[currency]
    print(f'[green][ {currency} @ {index:,} ][/green]')