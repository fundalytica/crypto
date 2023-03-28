from yahoo_fin import options
from yahoo_fin import stock_info as si
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama
init()

# Prompt the user for a stock symbol
symbol = input(Fore.YELLOW + "Please enter a stock symbol: " + Style.RESET_ALL)

# Get the current price of the stock
current_price = si.get_live_price(symbol)
print(Fore.WHITE + f"The current price of {symbol} is: {current_price}" + Style.RESET_ALL)

# Get all available expiration dates for the selected stock symbol
print(Fore.YELLOW + f"Loading expiration dates for {symbol}..." + Style.RESET_ALL, end="", flush=True)
expiration_dates = options.get_expiration_dates(symbol)
print(Fore.GREEN + "DONE" + Style.RESET_ALL)

# Print the expiration dates and total days to expiration
print(Fore.YELLOW + f"Available expiration dates for {symbol} options:" + Style.RESET_ALL)
expiration_table = []
for i, date in enumerate(expiration_dates):
    delta = datetime.strptime(date, '%B %d, %Y') - datetime.today()
    days_to_expiration = delta.days
    expiration_table.append([i+1, date, days_to_expiration])
print(tabulate(expiration_table, headers=["#", "Expiration Date", "Days to Expiration"], tablefmt="simple"))

# Prompt the user to select an expiration date
while True:
    try:
        selection = int(input(Fore.YELLOW + "\nPlease select an expiration date (enter a number): " + Style.RESET_ALL))
        if selection < 1 or selection > len(expiration_dates):
            raise ValueError
        break
    except ValueError:
        print(Fore.RED + "Invalid selection. Please try again." + Style.RESET_ALL)

expiration_date = expiration_dates[selection-1]

# Get the options chain for the selected expiration date
print(Fore.YELLOW + f"Loading options chain for {symbol} on {expiration_date}..." + Style.RESET_ALL, end="", flush=True)
options_chain = options.get_options_chain(symbol, expiration_date)
print(Fore.GREEN + "DONE" + Style.RESET_ALL)

# Get the calls and puts tables
calls = options_chain["calls"]
puts = options_chain["puts"]

# Print the calls and puts tables
days_to_expiration = expiration_table[selection-1][2]
print(Fore.YELLOW + f"\nOptions chain for {symbol} on {expiration_date} ({days_to_expiration} days to expiration):" + Style.RESET_ALL)

# Add the Cash Secured Put Yield column to the puts table
premium = puts["Last Price"] * 100
cost = puts["Strike"] * 100 - premium
cash_secured_put_yield = premium / (puts["Strike"] * 100) * 100
puts["Premium"] = premium
puts["Cost"] = cost
puts["Yield"] = cash_secured_put_yield
puts["Yield"] = puts["Yield"].apply(lambda x: "{:.2f}%".format(x))
puts["Annualized"] = cash_secured_put_yield / days_to_expiration * 365
puts["Annualized"] = puts["Annualized"].apply(lambda x: "{:.2f}%".format(x))

# deletions
del puts["Last Trade Date"]
del puts["Bid"]
del puts["Ask"]
del puts["Change"]
del puts["% Change"]

print(Fore.YELLOW + f"Loading calls table for {symbol} on {expiration_date}..." + Style.RESET_ALL, end="", flush=True)
calls_table = tabulate(calls.head(), headers=calls.columns, tablefmt="simple")
print(Fore.GREEN + "DONE" + Style.RESET_ALL)
print(Fore.GREEN + "\nCalls:" + Style.RESET_ALL)
print(calls_table)

print(Fore.YELLOW + f"Loading puts table for {symbol} on {expiration_date}..." + Style.RESET_ALL, end="", flush=True)
puts_table = tabulate(puts.head(), headers=puts.columns, tablefmt="simple")

print(puts)
for index, row in puts.iterrows():
    second_column_value = row[1]
    print(row)
    print(row[1])
    if (current_price * 0.9) <= second_column_value <= (current_price * 1.1):
        print(index)
        table_index = index + 2
        print(table_index)
        print(len(puts.index))
        if table_index < len(puts.index):
            puts_table = puts_table.split("\n")
            puts_table[table_index] = Fore.CYAN + puts_table[table_index] + Style.RESET_ALL  # Make the row green
            puts_table = "\n".join(puts_table)

print(Fore.GREEN + "DONE" + Style.RESET_ALL)
print(Fore.RED + "\nPuts:" + Style.RESET_ALL)
print(puts_table)

# Export the calls and puts tables to CSV files
# calls.to_csv(f"{symbol}_calls_{expiration_date}.csv", index=False)
# puts.to_csv(f"{symbol}_puts_{expiration_date}.csv", index=False)
# print(Fore.YELLOW + f"Exported calls and puts tables for {symbol} on {expiration_date} to CSV files." + Style.RESET_ALL)
