# Futures
# https://github.com/CryptoFacilities/WebSocket-v1-Python/blob/master/cfWebSocketApiV1.py
# https://support.kraken.com/hc/en-us/articles/360022635632-Subscriptions-WebSockets-API-
# https://support.kraken.com/hc/en-us/articles/360022635992-Ticker

from futures import Futures

import websocket
import _thread
import time
import sys
import json

from colorama import Fore

from utils import utils

ws = None

def ws_message(ws, message):
    # utils.cprint("\nWebSocket Thread: %s" % message, Fore.YELLOW)

    # print(message)

    m = json.loads(message)
    # print(m)

    if m['product_id']:
        if m['tag'] == 'semiannual':
            print(f"{m['product_id']} {m['tag']} {m['markPrice']} {m['premium']}")

    # SEND THE EMAIL !!!!!

def on_error(ws, error):
    utils.cprint(error, Fore.RED)

def ws_open(ws):
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

    utils.cprint(subscribe, Fore.CYAN)
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
        utils.cprint("Main Thread: %s" % time.ctime(time.time()), Fore.CYAN)

except KeyboardInterrupt:
    ws.close()
    print('\nBye :)\n')
    sys.exit(0)