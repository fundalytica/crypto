# https://www.mongodb.com/languages/python

import json
import pymongo
import argparse

CONNECTION_STRING = "mongodb://localhost:27017"

def get_database(connection_string, database):
    client = pymongo.MongoClient(connection_string)
    return client[database]

# def create_index(collection):
#     collection.create_index("symbol", unique=True)

# def insert_item(collection):
#     collection.insert_one({"symbol": "doge", "amount": 1000, "basis": 1})

# def print_df(assets):
#     from pandas import DataFrame
#     df = DataFrame(assets)

#     column_names = ["symbol", "amount", "cost"]
#     df = df.reindex(columns=column_names)

#     print(df)

def print_json(portfolio):
    json_data = json.dumps(portfolio)
    print(json_data)

# argparse
argparser = argparse.ArgumentParser(description="Crypto Portfolio")
argparser.add_argument("-db", help="database name", required=True)
argparser.add_argument("-user", help="user identifier", required=True)
args = argparser.parse_args()

if args.db:
    database = get_database(CONNECTION_STRING, args.db)

    collection_name = "crypto_portfolios"
    collection = database[collection_name]
    portfolio = collection.find_one({"email": args.user})

    if portfolio:
        for asset in portfolio["assets"]:
            del asset["_id"]

        del portfolio["_id"]
        del portfolio["__v"]
        del portfolio["email"]

        print_json(portfolio)
    else:
        print_json({"assets": []})

