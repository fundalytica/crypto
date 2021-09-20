# https://www.mongodb.com/languages/python

import json
import pymongo
import argparse

CONNECTION_STRING = "mongodb://localhost:27017"

def get_database(connection_string, database):
    client = pymongo.MongoClient(connection_string)
    return client[database]

def create_index(collection):
    collection.create_index("symbol", unique=True)

def insert_item(collection):
    collection.insert_one({"symbol": "doge", "amount": 1000, "basis": 1})

def print_cursor(collection):
    cursor = collection.find()

    for asset in cursor:
        print(asset["symbol"], asset["amount"], asset["basis"])

def print_df(collection):
    cursor = collection.find()

    from pandas import DataFrame
    df = DataFrame(cursor)

    del df["_id"]

    column_names = ["symbol", "amount", "basis"]
    df = df.reindex(columns=column_names)

    print(df)

def print_json(collection):
    cursor = collection.find()
    list_cur = list(cursor)

    for asset in list_cur:
        del asset["_id"]

    json_data = json.dumps(list_cur)
    print(json_data)

# argparse
argparser = argparse.ArgumentParser(description="Crypto Portfolio")
argparser.add_argument("-db", help="database name")
args = argparser.parse_args()

if args.db:
    database = get_database(CONNECTION_STRING, args.db)

    collection_name = "crypto_portfolio"
    collection = database[collection_name]
    print_json(collection)