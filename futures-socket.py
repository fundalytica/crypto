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

from colorama import Fore
from datetime import datetime, timezone, timedelta

from utils import utils, mailer

ws = None

futures = None
email_sent = False

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

    m = json.loads(message)
    # print(m)

    crypto_colors = {'XBT':Fore.GREEN, 'ETH':Fore.CYAN}

    if m['product_id']:
        if m['tag'] == 'semiannual':
            # XBT:USD FI_XBTUSD_210924 semiannual 38580.25 0.5% in 127d 1.4%

            maturity = datetime.fromtimestamp(int(m['maturityTime']) / 1000, timezone.utc)
            delta = futures.days_left(maturity)
            days = utils.days_delta_fractional(delta)

            annualized = m['premium'] / days * 365

            crypto = m['pair'][:3]
            color = crypto_colors[crypto]
            utils.cprint(f"{m['pair']} {m['product_id']} {m['tag']} {m['markPrice']} {m['premium']}% in {int(days)}d {round(annualized,1)}%", color)

    # CONDITIONS FOR SENDING EMAIL
    # send_email()
    # send_sms()

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

try:
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