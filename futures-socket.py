# Futures
# https://github.com/CryptoFacilities/WebSocket-v1-Python/blob/master/cfWebSocketApiV1.py
# https://support.kraken.com/hc/en-us/articles/360022635632-Subscriptions-WebSockets-API-
# https://support.kraken.com/hc/en-us/articles/360022635992-Ticker

import websocket
import _thread
import time

def ws_message(ws, message):
    print("WebSocket Thread: %s" % message)

def ws_open(ws):
    subscribe = '{"event": "subscribe", "feed": "ticker", "product_ids": ["PI_XBTUSD","PI_ETHUSD"]}'
    ws.send(subscribe)

def ws_thread(*args):
    ws = websocket.WebSocketApp("wss://futures.kraken.com/ws/v1", on_open = ws_open, on_message = ws_message)
    ws.run_forever()

# Start a new thread for the WebSocket interface
_thread.start_new_thread(ws_thread, ())

# Continue other (non WebSocket) tasks in the main thread
while True:
    time.sleep(5)
    print("Main Thread: %d" % time.time())