# Futures
# https://github.com/CryptoFacilities/WebSocket-v1-Python/blob/master/cfWebSocketApiV1.py
# https://support.kraken.com/hc/en-us/articles/360022635632-Subscriptions-WebSockets-API-
# https://support.kraken.com/hc/en-us/articles/360022635992-Ticker

from futures import Futures

# from mailer import Mailer

import websocket
import _thread
import time
import sys
import json

from colorama import Fore, Style
from datetime import datetime, timezone, timedelta

from utils import utils, mailer

from pymongo import MongoClient
mongo = MongoClient('mongodb://localhost')
db=mongo.fundalytica

ws = None

futures = None
email_sent = False

# TODO: frontend entries
# TODO: daemonize
# TODO: send email
# TODO: frontend sms

alerts = None

def send_email():
    try:
        global email_sent
        if not email_sent:
            recipients = ['fotios@fundalytica.com']
            subject = 'Hello'
            text = 'This is Mailgun!'
            response = mailer.send_simple_message(recipients, subject, text)
            email_sent = True
            print(response)
            print(response.text)
            utils.cprint('Email Sent!', Fore.GREEN)
    except Exception as e:
        print(e)

def ws_message(ws, message):
    # utils.cprint("\nWebSocket Thread: %s" % message, Fore.YELLOW)
    # print(message)

    message = json.loads(message)
    product_id = message.get('product_id')

    if product_id:
        pair = message.get('pair')
        tag = message.get('tag')

        if(not (pair and tag)):
            return

        alerts=db.alerts.find({'sent': 0, 'pair': pair, 'period': tag})
        process_alerts(alerts, message)

def process_alerts(alerts, message):
    # print(len(alerts))
    # if(len(alerts) == 0):
    #     return

    product_id = message.get('product_id')
    pair = message.get('pair')
    tag = message.get('tag')
    premium = message.get('premium')
    markPrice = message.get('markPrice')
    maturityTime = message.get('maturityTime')

    if(not (premium and markPrice and maturityTime)):
        return

    # if pair != 'XBT:USD':
    #     return
    # if tag != 'semiannual':
    #     return

    maturity = datetime.fromtimestamp(int(maturityTime) / 1000, timezone.utc)
    delta = futures.days_left(maturity)
    days = utils.days_delta_fractional(delta)

    annualized = premium / days * 365

    crypto = pair[:3]

    crypto_colors = {'XBT':Fore.YELLOW, 'ETH':Fore.CYAN}
    color = crypto_colors[crypto]

    # XBT:USD FI_XBTUSD_210924 semiannual 38580.25 0.5% in 127d 1.4%
    print(f"\n- {color}{pair} {Style.RESET_ALL}{product_id} {tag} {markPrice} {premium}% in {int(days)}d {round(annualized,1)}%")

    try:
        # utils.cprint(f'Annualized: {annualized}', Fore.YELLOW)
        # utils.cprint(f'\n[ Alerts ({len(alerts)}) ]', Fore.CYAN)
        # utils.pretty_print(alerts)

        values = { 'markPrice': markPrice, 'premium': premium, 'annualized': annualized }
        # print(values)

        operator_lambda = { "=": (lambda x, y: x == y), "<": (lambda x, y: x < y), ">": (lambda x, y: x > y) }

        # def item_pass(item, pair, tag):
        #     # print(f'find {pair} {tag}')
        #     item_pair = item.get(pair)
        #     item_tag = item_pair.get(tag) if item_pair else None
        #     result = item_pair and item_tag
        #     # if result:
        #     #     utils.cprint(f'Item Pass {item}', Fore.GREEN)
        #     # else:
        #     #     utils.cprint(f'Item Reject {item} {pair}:{item_pair} {tag}:{item_tag}', Fore.WHITE)
        #     return result

        # def item_value_pass(item, pair, tag):
        #     dictionary = item.get(pair).get(tag)

        #     targetProperty = dictionary.get('property')

        #     currentValue = values.get(targetProperty)
        #     operator = dictionary.get('operator')
        #     targetValue = dictionary.get('value')

        #     result = operator_lambda[operator](currentValue, targetValue)
        #     # if result:
        #     #     utils.cprint(f'Value Pass {currentValue} {operator} {targetValue} {result}', Fore.MAGENTA)
        #     # else:
        #     #     utils.cprint(f'Value Reject {currentValue} {operator} {targetValue} {result}', Fore.WHITE)
        #     return result

        for item in alerts:
            _id = item.get('_id')

            targetProperty = item.get('property')
            operator = item.get('operator')
            targetValue = item.get('value')
            currentValue = values.get(targetProperty)
            qualified = operator_lambda[operator](currentValue, targetValue)

            if qualified:
                print(f'{item.get("property")} {item.get("operator")} {item.get("value")}')
                utils.cprint(f'Qualified / Notified', Fore.GREEN)
                # print('qualified')
                # result = db.alerts.delete_one({'_id': _id})
                result = db.alerts.update_one(item, { '$set': { 'sent': 1 } })
                utils.cprint(f'DB Modified {result.modified_count}', Fore.CYAN)
                # print(result.deleted_count)
            # else:
            #     utils.cprint('Unqualified', Fore.RED)


        # # utils.cprint(f'\n[ Qualification Checks ]', Fore.CYAN)
        # lambda_filter = lambda item: item_pass(item, pair, tag) and item_value_pass(item, pair, tag)
        # qualified = list(filter(lambda_filter, alerts))
        # if len(qualified):
        #     utils.cprint(f'\n[ Qualified ({len(qualified)}) ]', Fore.CYAN)
        #     utils.pretty_print(qualified)
        #     utils.cprint(f'\n[ Send Notification ]', Fore.CYAN)
        #     count = 0
        #     for item in qualified:
        #         utils.cprint(f'#{count+1} Email Sent', Fore.GREEN)
        #         utils.cprint(f'#{count+1} SMS Sent', Fore.GREEN)
        #         alerts.remove(item)
        #         count += 1

        # utils.cprint(f'\n[ Alerts Now ({len(alerts)}) ]', Fore.CYAN)
        # utils.pretty_print(alerts)
    except Exception as e:
        print(f'Error -> {e}')

def on_error(ws, error):
    utils.cprint(error, Fore.RED)

def ws_open(ws):
    global futures
    futures = Futures()
    all_symbols = futures.all_futures_symbols()

    ids = []
    for pair in all_symbols:
        pair_symbols = all_symbols[pair]
        for period in pair_symbols:
            symbol = pair_symbols[period]
            ids.append(f'"{symbol}"')
    product_ids = f'[{",".join(ids)}]'

    # subscribe = '{"event": "subscribe", "feed": "ticker", "product_ids": ["PI_XBTUSD","PI_ETHUSD"]}'
    subscribe = '{"event": "subscribe", "feed": "ticker", "product_ids": %s}' % product_ids

    utils.cprint(f'subscribe {subscribe}', Fore.MAGENTA)

    ws.send(subscribe)

def on_close(ws):
    utils.cprint("WebSocket Closed", Fore.CYAN)

def ws_thread(*args):
    global ws
    ws = websocket.WebSocketApp("wss://futures.kraken.com/ws/v1", on_open = ws_open, on_message = ws_message, on_error = on_error, on_close = on_close)
    ws.run_forever()

def add_dummy_db_data():
    data = [
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'XBT:USD', 'period': 'semiannual', 'property': 'markPrice', 'operator': '>', 'value': 5 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'ETH:USD', 'period': 'semiannual', 'property': 'markPrice', 'operator': '>', 'value': 5 },

        { 'user': 'fundalytica', 'sent': 0, 'pair': 'XBT:USD', 'period': 'month', 'property': 'premium', 'operator': '>', 'value': 0.05 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'XBT:USD', 'period': 'quarter', 'property': 'premium', 'operator': '>', 'value': 0.05 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'XBT:USD', 'period': 'quarter', 'property': 'premium', 'operator': '>', 'value': 0.05 },

        { 'user': 'fundalytica', 'sent': 0, 'pair': 'XBT:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 10 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'XBT:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 10 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'ETH:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 5 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'ETH:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 5 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'ETH:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 5 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'ETH:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 5 },
        { 'user': 'fundalytica', 'sent': 0, 'pair': 'ETH:USD', 'period': 'semiannual', 'property': 'annualized', 'operator': '<', 'value': 10 },
    ]

    # purge
    db.alerts.delete_many({'user': 'fundalytica'})
    # add
    db.alerts.insert_many(data)

try:
    add_dummy_db_data()

    # Start WebSocket Thread
    _thread.start_new_thread(ws_thread, ())

    # Main Thread
    while True:
        time.sleep(5)
        utils.cprint("Main Thread: %s" % time.ctime(time.time()), Fore.MAGENTA)

except KeyboardInterrupt:
    ws.close()
    print('\nBye :)\n')
    sys.exit(0)