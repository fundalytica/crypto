#!/usr/bin/python3

import json

import os
import argparse

from functools import reduce

import string
import csv
import pprint
pp = pprint.PrettyPrinter(compact=True)

import calendar
from datetime import datetime

from tabulate import tabulate
from colorama import init,Fore,Back,Style
init(autoreset=True)

from fundalytica_utils import utils

ASSET_CATEGORY_STOCKS_LLC = 'Stocks - Held with Interactive Brokers (U.K.) Limited carried by Interactive Brokers LLC'
ASSET_CATEGORY_STOCKS = 'Stocks'
ASSET_CATEGORY_OPTIONS = 'Equity and Index Options'
ASSET_CATEGORY_BONDS = 'Bonds'
ASSET_CATEGORY_FOREX = 'Forex'
ALL_ASSET_CATEGORIES = [ASSET_CATEGORY_STOCKS, ASSET_CATEGORY_OPTIONS, ASSET_CATEGORY_BONDS, ASSET_CATEGORY_FOREX]

JPY_SYMBOLS = ['9684.T']
GBP_SYMBOLS = ['VMID','VUKE']
SGX_SYMBOLS = ['A17U','A68U','A68U.OLD','ACV','AJBU','AU8U','AU8URTS','BUOU','C38U','C61U','CLR','CMOU','CNNU','CRPU','D5IU','HMN','J85','J91U','J91UNR','K2LU','K71U','M44U','ME8U','N2IU','N2IUNR','ND8U','P40U','Q1P','Q5T','RW0U','SK7','T82U','TS0U','UD1U']
# FOREX_SYMBOLS = ['USD.JPY','USD.SGD','EUR.AUD','EUR.GBP','EUR.USD','AUD.SGD','GBP.USD']
NON_USD_SYMBOLS = JPY_SYMBOLS + GBP_SYMBOLS + SGX_SYMBOLS # need to parse

class IBCSVParser:
    def __init__(self):
        self.rows = []

    def clear(self):
        # print(f'{Fore.CYAN}> - *{Style.RESET_ALL}')
        self.rows = []

    def add(self, path):
        # print(f'{Fore.CYAN}> + {path}{Style.RESET_ALL}')
        with open(path, encoding='utf-8-sig') as csvfile: # encode with BOM (byte order mark)
            for row in csv.reader(csvfile):
                # replace ASSET_CATEGORY_STOCKS_LLC with ASSET_CATEGORY_STOCKS
                for index, column in enumerate(row):
                    if ASSET_CATEGORY_STOCKS_LLC in column:
                        row[index] = column.replace(ASSET_CATEGORY_STOCKS_LLC, ASSET_CATEGORY_STOCKS)

                self.rows.append(row)

    def report_period(self):
        statement = self.group_with_column_index(self.rows, 0, 'Statement')
        header, data = self.group_with_column_name(statement, 'Field Name', 'Period')
        start, end = data[-1].split(' - ')
        return [start, end]

    def report_generated(self):
        statement = self.group_with_column_index(self.rows, 0, 'Statement')
        header, data = self.group_with_column_name(statement, 'Field Name', 'WhenGenerated')
        return data[-1]

    def date(self, date):
        date = datetime.strptime(date, '%Y-%m-%d, %H:%M:%S')
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return date

    def expiration_date(self, symbol):
        if len(symbol.split()) == 4: # e.g. WORK 17APR20 30.0 P
            expiration = symbol.split()[1]
            return datetime.strptime(expiration, '%d%b%y')

        if len(symbol.split()) == 2: # e.g. TSLA 200731P01300000
            expiration = symbol.split()[1][:6]
            return datetime.strptime(expiration, '%y%m%d')

        return None

    def expiration_format(self, symbol):
        if len(symbol.split()) == 4: # e.g. WORK 17APR20 30.0 P
            expiration = symbol.split()[1]
            return expiration

        if len(symbol.split()) == 2: # e.g. TSLA 200731P01300000
            expiration = symbol.split()[1][:6]
            year = expiration[0:2]
            month = expiration[2:4]
            date = expiration[4:6]
            month = calendar.month_abbr[int(month)].upper()
            return f'{date}{month}{year}'

        return symbol

    def strike(self, symbol):
        if len(symbol.split()) == 4: # e.g. WORK 17APR20 30.0 P
            return symbol.split()[2]

        if len(symbol.split()) == 2: # e.g. TSLA 200731P01300000
            strike = float(symbol.split()[1][7:]) / 1000
            return strike

        return None

    def group_with_column_index(self, data, column_index, value):
        # e.g. rows at column index 0, having a value of 'Trades'
        return list(filter(lambda x: x[column_index] == value, data))

    def cash_report_group(self):
        return self.group_with_column_index(self.rows, 0, 'Cash Report')

    def interest_group(self):
        return self.group_with_column_index(self.rows, 0, 'Interest')

    def performance_group(self):
        return self.group_with_column_index(self.rows, 0, 'Realized & Unrealized Performance Summary')

    def trades_group(self):
        return self.group_with_column_index(self.rows, 0, 'Trades')

    def open_positions_group(self):
        return self.group_with_column_index(self.rows, 0, 'Open Positions')

    def performance_summary_group(self):
        return self.group_with_column_index(self.rows, 0, 'Mark-to-Market Performance Summary')

    def group_with_column_name(self, data, column_name, value, value_partial=False):
        # e.g. rows at column index derived by name 'Asset Category' position at header, having a value of 'Stocks'
        # e.g. rows at column index derived by name 'Symbol' position at header, having a value of 'AAPL'

        header = data[0]
        index = header.index(column_name)

        if not value_partial:
            data = list(filter(lambda x: x[index] == value, data))
        else:
            # data = list(filter(lambda x: x[index].split()[0] == value, data))
            data = list(filter(lambda x: x[index].find(value) != -1, data))

        data.insert(0, header) # restore header after filtering

        return data

    def symbols(self, data=None, partial_value=False):
        data = self.performance_group() if data is None else data

        header = data[0]
        column = header.index('Symbol')

        data = data[1:]                                         # skip header
        data = list(map(lambda x: x[column], data))             # map to single column
        data = list(filter(lambda x: 'Symbol' not in x, data))  # remove Symbol occurences due to multiple headers
        data = list(filter(lambda x: x != '', data))            # remove empty strings

        if partial_value is True:
            data = list(map(lambda x: x.split()[0], data))      # simplify options/bonds symbols

        data = list(set(data))                                  # unique
        data = sorted(data)                                     # sort

        return data

    def trades_symbols(self, currency='USD'):
        trades = self.trades_group()
        trades = self.group_with_column_name(trades, 'Currency', currency)

        stock_trades = parser.group_with_column_name(trades, 'Asset Category', ASSET_CATEGORY_STOCKS)
        stock_symbols = parser.symbols(stock_trades)

        option_symbols = self.option_trades_symbols(currency)

        symbols = stock_symbols + option_symbols

        symbols = list(set(symbols))    # unique
        symbols = sorted(symbols)       # sort

        return symbols

    def option_trades_symbols(self, currency='USD'):
        trades = self.trades_group()
        trades = self.group_with_column_name(trades, 'Currency', currency)

        option_trades = parser.group_with_column_name(trades, 'Asset Category', ASSET_CATEGORY_OPTIONS)
        option_symbols = parser.symbols(option_trades, partial_value=True)

        option_symbols = list(set(option_symbols))    # unique
        option_symbols = sorted(option_symbols)       # sort

        return option_symbols

    def date_range(self):
        trades = self.trades_group()

        headers = trades[0]
        date_index = headers.index('Date/Time')

        min_date = None
        max_date = None

        trades = parser.group_with_column_name(trades, 'DataDiscriminator', 'Order')
        for trade in trades[1:]:
            trade_date = parser.date(trade[date_index])
            min_date = trade_date if min_date is None else min(min_date, trade_date)
            max_date = trade_date if max_date is None else max(max_date, trade_date)

        return (min_date, max_date) if (min_date is not None and max_date is not None) else None

    # e.g. return VANGUARD TOTAL STOCK MKT ETF for symbol VTI
    # if a report has only option trades the stock symbol description will not be available
    def stock_description(self, symbol):
        # Financial Instrument Information
        information = self.group_with_column_index(self.rows, 0, 'Financial Instrument Information')
        # Stocks
        information = parser.group_with_column_name(information, 'Asset Category', ASSET_CATEGORY_STOCKS)
        # Header - Financial Instrument Information,Header,Asset Category,Symbol,Description,Conid,Security ID,Multiplier,Type,Code
        header = information[0]
        # Indices
        symbol_index = header.index('Symbol')
        description_index = header.index('Description')

        # Filter by symbol
        information = list(filter(lambda x: x[symbol_index] == symbol, information))

        if len(information) != 0:
            # Keep one - Repeating Financial Instrument Information when using multiple statements
            # Financial Instrument Information,Data,Stocks,VTI,'VANGUARD TOTAL STOCK MKT ETF
            # Financial Instrument Information,Data,Stocks,VTI,'VANGUARD TOTAL STOCK MKT ETF
            information = information[0]
            information = information[description_index]
            return information

    def total_with_column_name(self, data, column_name):
        header = data[0]
        index = header.index(column_name)

        total = 0
        for row in data[1:]: # skip header row
            total = total + float(row[index])

        return total

def displayDot():
    print(f'\n{Fore.YELLOW}.{Style.RESET_ALL}\n')

def displayTradingPeriod():
    # Statement,Header,Field Name,Field Value
    # Statement,Data,Period,"January 2, 2020 - July 17, 2020"

    data = parser.group_with_column_index(parser.rows, 0, 'Statement')
    data = parser.group_with_column_name(data, 'Field Name', 'Period')

    header = data[0]
    index = header.index('Field Value')

    period = data[1][index]
    start = period.split(' - ')[0]
    end = period.split(' - ')[1]

    date = datetime.strptime(end, '%B %d, %Y')
    days = abs((date - datetime.now()).days)

    out = f'{Fore.CYAN}{start} - {end}{Style.RESET_ALL}'

    if(datetime.now().year == date.year):
        out += f' ({days}d ago)'
    print(out)

def displayCashReport():
    # cash_categories = ['Dividends','Withholding Tax','Broker Interest Paid and Received','Bond Interest Paid and Received','Commissions','Other Fees']
    cash_categories = ['Dividends','Withholding Tax','Broker Interest Paid and Received','Commissions','Other Fees']

    for cash_category in cash_categories:
        data = parser.cash_report_group()
        data = parser.group_with_column_name(data, 'Currency Summary', cash_category)

        if len(data) > 1:
            data = parser.group_with_column_name(data, 'Currency', 'Base Currency Summary')

            header = data[0]
            index = header.index('Total')
            total = float(data[1][index])

            print(f'\n{Fore.GREEN}[ {cash_category} ]{Style.RESET_ALL}')
            if total != 0:
                print(f'{total:,.0f}')

def displayBondCouponPayments():
    description = 'Bond Coupon Payment'

    data = parser.interest_group()
    data = parser.group_with_column_name(data, 'Description', description, True)

    if len(data) > 1:
        header = data[0]
        index = header.index('Amount')

        # only amount
        data = list(map(lambda x: float(x[index]), data[1:]))
        # reduce total
        total = reduce(lambda x, y: x + y, data)

        print(f'\n{Fore.GREEN}[ {description} ]{Style.RESET_ALL}')
        if total != 0:
            print(f'{total:,.0f}')

def displayPerformance(asset_categories, symbols, total_types):
    def displayTotals(data, total_types):
        for type in total_types:
            total = parser.total_with_column_name(data, type)
            # if total != 0:
            print(f'- {type.split()[0]}: {total:,.0f}')

    for asset_category in asset_categories:
        print(f'\n{Fore.GREEN}[ {asset_category} ]{Style.RESET_ALL}')
        performance = parser.group_with_column_name(parser.performance_group(), 'Asset Category', asset_category)

        if len(symbols) == 0:
            displayTotals(performance, total_types)

        if symbols == '*':
            symbols = parser.symbols(performance)                           # get all symbols
            # symbols = filter(lambda x: x not in NON_USD_SYMBOLS, symbols)   # filter non USD

        for symbol in symbols:
            print(f'{Fore.YELLOW}( {symbol} ){Style.RESET_ALL}')
            symbol_partial = asset_category in [ASSET_CATEGORY_OPTIONS, ASSET_CATEGORY_BONDS]
            data = parser.group_with_column_name(performance, 'Symbol', symbol, symbol_partial)

            displayTotals(data, total_types)

def runPerformance(total_types=['Realized Total', 'Unrealized Total']):
    # all asset categories
    displayPerformance(ALL_ASSET_CATEGORIES, [], total_types)
    # displayDot()
    # all stocks
    # displayPerformance([ASSET_CATEGORY_FOREX], '*', ['Realized Total', 'Unrealized Total'])
    # displayDot()
    # all options
    # displayPerformance([ASSET_CATEGORY_OPTIONS], '*', ['Realized Total', 'Unrealized Total'])
    # displayDot()
    # single symbol stocks and options
    # displayPerformance([ASSET_CATEGORY_STOCKS, ASSET_CATEGORY_OPTIONS], ['DAL'], ['Realized Total', 'Unrealized Total'])
    # displayDot()

def drop_columns(drop, header, data):
    # drop from rows
    def map_row(row):
        r = []
        for index, value in enumerate(row):
            if header[index] not in drop:
                r.append(value)
        return r

    data = [map_row(row) for row in data]

    # drop from header (list comprehension to maintain order)
    header = [x for x in header if x not in drop]

    return [header, data]

def displayTrades(symbol, verbose=False):
    # all trades
    data = parser.trades_group()
    # orders only, no totals rows
    data = parser.group_with_column_name(data, 'DataDiscriminator', 'Order')
    # USD trades only
    data = parser.group_with_column_name(data, 'Currency', 'USD')

    # filter stocks
    stocks = parser.group_with_column_name(data, 'Asset Category', ASSET_CATEGORY_STOCKS, value_partial=True)
    # filter by symbol
    stocks = parser.group_with_column_name(stocks, 'Symbol', symbol)

    # filter options
    options = parser.group_with_column_name(data, 'Asset Category', ASSET_CATEGORY_OPTIONS)
    # filter by partial symbol
    options = parser.group_with_column_name(options, 'Symbol', symbol, True)

    # retain header
    header = stocks[0]

    # remove header
    stocks.pop(0)
    options.pop(0)
    # merge stocks and options
    trades = stocks + options

    # sort by execution date
    def date_sort(elem):
        index_date = header.index('Date/Time')
        index_category = header.index('Asset Category')
        return (parser.date(elem[index_date]), elem[index_category])

    trades = sorted(trades, key=date_sort, reverse=False)

    # two CSV versions encountered, one contains 'Realized P/L %' column, one does not
    # simple solution, drop realized P/L % from header and trades
    # rough hack using header and trades length
    drop_index = 14 # 'Realized P/L %'
    if len(header) == 17:
        del header[drop_index]
    for trade in trades:
        if len(trade) == 17:
            del trade[drop_index]

    # drop columns
    drop = ['Trades','Header','DataDiscriminator','Currency','C. Price','MTM P/L']
    drop.append('Realized P/L %') # LLC
    header, trades = drop_columns(drop, header, trades)

    # header debug
    # print(header)

    # string mappings
    str_categories = { 'Stocks': 'Stock', 'Equity and Index Options': 'Option' }
    # str_categories[ASSET_CATEGORY_STOCKS_LLC] = str_categories['Stocks']
    str_codes = {
        'O': 'Open', 'O;P': 'Open', 'O;PI': 'Open', 'CP;O': 'Open',
        'C': 'Close', 'C;P': 'Close', 'C;Ep': 'Expired.Close',
        'A;O': 'Assignment.Open', 'A;C': 'Assignment.Close',
        'C;O': 'Close & Open', 'C;O;P': 'Close & Open', 'CP;O;P': 'Close & Open',
        'Ca': 'Cancelled',
        'C;PI': 'Price Improvement'
    }
    str_rights = { 'C': 'Call', 'P': 'Put' }

    table_trades = []
    table_out = []

    total_stock = 0
    total_call_options = 0
    total_put_options = 0
    total_proceeds = 0
    total_fees = 0
    total_realized = 0
    current_average = 0
    real_average = 0

    # trades = trades[:5]

    for trade in trades:
        table_trades.append(trade)

        headers = []
        strings = []

        # get indices
        index_date = header.index('Date/Time')
        index_category = header.index('Asset Category')
        index_symbol = header.index('Symbol')
        index_qty = header.index('Quantity')
        index_price = header.index('T. Price')
        index_proceeds = header.index('Proceeds')
        index_fee = header.index('Comm/Fee')
        index_realized = header.index('Realized P/L')
        index_code = header.index('Code')

        # get values
        val_date = parser.date(trade[index_date])
        val_category = trade[index_category]
        val_symbol = trade[index_symbol]
        val_qty = float(trade[index_qty].replace(',','')) # remove comma separated numbers
        val_price = float(trade[index_price])
        val_proceeds = float(trade[index_proceeds])
        val_fee = float(trade[index_fee])
        val_realized = float(trade[index_realized])
        val_code = trade[index_code]
        val_right = None

        # save
        stock_before = total_stock

        # totals
        if val_category == 'Equity and Index Options':
            if len(val_symbol.split()) == 4: # e.g. WORK 17APR20 30.0 P
                val_right = val_symbol.split()[-1]

            if len(val_symbol.split()) == 2: # e.g. TSLA 200731P01300000
                val_right = val_symbol.split()[1][6]

            if val_right not in ['P','C']:
                print(f'{Fore.RED} Unknown {val_category} Format: {val_symbol}{Style.RESET_ALL}')

            if val_right == 'P':
                total_put_options += val_qty
            if val_right == 'C':
                total_call_options += val_qty
        else:
            total_stock += val_qty
        total_proceeds += val_proceeds
        total_fees += val_fee
        total_realized += val_realized

        # output average price
        out_average = '-'
        if val_category == ASSET_CATEGORY_STOCKS:
            # stock purchase only, on sale the average price remains the same
            if val_qty > 0:
                # total cost before the trade
                cost_before = stock_before * current_average

                # total stock after the trade
                stock_after = stock_before + val_qty

                # position available, calculate new average
                if stock_after != 0:
                    # total cost after the trade
                    cost_after = val_proceeds + cost_before
                    # new average
                    current_average = cost_after / stock_after

                # position liquidated
                if stock_after == 0:
                    # average becomes 0
                    current_average = 0

            out_average = f'{-round(current_average, 2):,}'

        # output real average
        # current average but taking into account the realized p/l as well
        out_real_average = '-'
        if total_realized != 0:
            if total_stock != 0:
                cost_total = current_average * total_stock
                real_total = cost_total + total_realized
                real_average = real_total / total_stock
                # out_real_average = f'{round(cost_total, 2):,} {round(total_realized, 2):,} {round(real_total, 2):,} {round(real_average, 2):,}'
                # out_real_average = f'{-round(real_average, 2):,}'

        # output date
        out_date = val_date.strftime("%d-%b-%y")

        # output category
        out_category = str_categories[val_category]
        # show option right next to option category
        if val_category == 'Equity and Index Options':
            out_right = str_rights[val_right]
            out_category = out_right
        # append current totals
        if val_category == 'Equity and Index Options':
            out_category = f'{out_category}'
        else:
            out_category = f'{Back.BLUE}{out_category}{Style.RESET_ALL}'

        # output_position
        out_position = '-'
        if val_category == 'Equity and Index Options':
            if val_right == 'P':
                out_position = f'{total_put_options}'
            if val_right == 'C':
                out_position = f'{total_call_options}'
        else:
            out_position = f'{Back.BLUE}{total_stock}{Style.RESET_ALL}'

        # output code
        out_code = str_codes[val_code]

        # output quantity
        out_qty = str(val_qty)
        # do not show buy or sell string if an option was closed through assignment
        if val_category == 'Equity and Index Options' and ('A' in val_code or 'Ep' in val_code):
            out_qty = str(val_qty)
        else:
            out_qty = 'Buy' if val_qty > 0 else 'Sell'
            out_qty = f'{out_qty} {val_qty}'

        #output price
        out_price = '-'
        if val_price != 0:
            out_price = f'@ {val_price}'

        # output expiration
        out_expiration = '-'
        if val_category == 'Equity and Index Options':
            val_expiration = parser.expiration_format(val_symbol)
            out_expiration = val_expiration

            if 'O' in val_code:
                val_duration = (parser.expiration_date(val_symbol) - val_date).days + 1 # include expiration day (trading day)
                out_expiration = f'{out_expiration} {val_duration}d'
                val_days_remaining = (parser.expiration_date(val_symbol) - datetime.now()).days
                if val_days_remaining > 0:
                    out_expiration = f'{Fore.CYAN}{out_expiration} ({val_days_remaining}d){Style.RESET_ALL}'

        # output strike
        out_strike = '-'
        if val_category == 'Equity and Index Options':
            val_strike = parser.strike(val_symbol)
            out_strike = val_strike

        # output proceeds
        out_proceeds = '-'
        if val_proceeds != 0:
            out_proceeds = 'Made' if val_proceeds > 0 else 'Spent'
            out_proceeds = f'{out_proceeds} {val_proceeds:,.0f}'
            if val_category == 'Equity and Index Options' and val_code == 'O':
                val_strike = parser.strike(val_symbol)
                val_capital = float(val_strike) * abs(val_qty) * 100
                val_duration = (parser.expiration_date(val_symbol) - val_date).days
                val_yield = val_proceeds / val_capital / val_duration * 365
                out_proceeds = f'{out_proceeds} ({val_yield:,.1%})'

        # output fees
        out_fee = '-'
        if val_fee != 0:
            out_fee = f'{val_fee:.2f}'

        # output realized
        out_realized = '-'
        if val_realized != 0:
            out_realized = val_realized
            out_realized = f'{"Profit" if float(val_realized) > 0 else "Loss"} {val_realized:,.0f}'
            out_realized += f' / {round(total_realized):,}'
        if val_category == ASSET_CATEGORY_STOCKS:
            if val_code == 'A;O':
            	out_realized = 'On Close (Put+Stock)'
            if val_code == 'A;C':
                out_realized = f'{out_realized} (Options+Stock)'

        headers.append('Category'); strings.append(out_category)
        headers.append('Action'); strings.append(out_code)
        headers.append('Quantity'); strings.append(out_qty)
        headers.append('Price'); strings.append(out_price)
        headers.append('Position'); strings.append(out_position)
        #headers.append('Average'); strings.append(out_average)
        #headers.append('RealAverage™'); strings.append(out_real_average)
        headers.append('Date'); strings.append(out_date)
        headers.append('Expiration'); strings.append(out_expiration)
        headers.append('Strike'); strings.append(out_strike)
        headers.append('Proceeds'); strings.append(out_proceeds) # fee exclusive
        headers.append('Realized'); strings.append(out_realized) # fee inclusive
        #headers.append('Fee'); strings.append(out_fee)

        # color yellow assignment
        if 'A' in val_code:
            strings = [f'{Fore.YELLOW}{x}{Style.RESET_ALL}' for x in strings]
        # color green expiration
        if 'Ep' in val_code:
            strings = [f'{Fore.GREEN}{x}{Style.RESET_ALL}' for x in strings]

        table_out.append(strings)

    # get highest / lowest
    lowest = None
    highest = None
    for trade in table_trades:
        index_category = header.index('Asset Category')
        index_price = header.index('T. Price')

        if trade[index_category] == ASSET_CATEGORY_STOCKS:
            price = float(trade[index_price])
            lowest = price if lowest is None else min(price, lowest)
            highest = price if highest is None else max(price, highest)

    def printVerbose():
        print(header_string)
        print()
        #print(tabulate(table_trades, headers=header))
        #print()
        print(tabulate(table_out, headers=headers))
        print()
        print(detail_string)

    header_string = f'{Fore.YELLOW}( {symbol} - {parser.stock_description(symbol)} ){Style.RESET_ALL}'

    # stock should be zero in this case
    # but there are exceptions
    if round(total_proceeds + total_fees,2) == round(total_realized,2):
        if total_realized > 0:
            header_string += f' {Fore.GREEN}Profit: {round(total_realized,2):,}{Style.RESET_ALL}'
        if total_realized < 0:
            header_string += f' {Fore.RED}Loss: {round(total_realized,2):,}{Style.RESET_ALL}'

        detail_string = f'{Fore.WHITE}Trades {len(table_out)}{Style.RESET_ALL}'
        if lowest is not None:
            detail_string += f'{Fore.WHITE} | Lowest {round(lowest):,} | Highest {round(highest):,}{Style.RESET_ALL}'

        if verbose is False:
            print(header_string)
            print(detail_string)
        else:
            printVerbose()
    else:
        detail_string = f'{Fore.YELLOW}{Back.BLUE if total_stock else ""}Stock {total_stock:,.0f}{Back.RESET} | Puts {total_put_options:,.0f}, Calls {total_call_options:,.0f}{Style.RESET_ALL}'

        detail_string += f'\n{Fore.WHITE}Trades {len(table_out)}{Style.RESET_ALL}'
        if lowest is not None:
            detail_string += f'{Fore.WHITE} | Lowest {round(lowest):,} | Highest {round(highest):,}{Style.RESET_ALL}'

        detail_string += f'\n{Fore.CYAN}Proceeds {round(total_proceeds):,} | Realized {round(total_realized):,} | Fees {round(total_fees):,}{Style.RESET_ALL}'

        if total_stock:
            detail_string += f'\n{Fore.CYAN}Average {-round(current_average, 2):,} | RealAverage™ {-round(real_average, 2):,}{Style.RESET_ALL}'

        if verbose is True:
            printVerbose()
        else:
            header_string += ' ' + detail_string
            print(header_string)

    # global all_trades; all_trades += len(trades)
    # global all_realized; all_realized += total_realized
    # global all_fees; all_fees += total_fees

def runTrades():
    print(f'\n{Fore.GREEN}[ Trades ]{Style.RESET_ALL}')

    symbols = parser.trades_symbols()

    # global all_trades; all_trades = 0
    # global all_realized; all_realized = 0
    # global all_fees; all_fees = 0
    for symbol in symbols:
        displayTrades(symbol)
    # print(f'\n{Back.MAGENTA}Trades {all_trades:,} | Realized {round(all_realized):,} | Fees {round(all_fees):,}{Back.RESET}')
    print(f'\n{Back.MAGENTA}Trades {all_trades:,} | Realized {round(all_realized):,}{Back.RESET}')

    # displayTrades('TSLA', verbose=True)

    date_range = parser.date_range()
    if date_range is not None:
        start = date_range[0]
        end = date_range[1]
        days = (end - start).days + 1
        print(f'\n{Back.WHITE}{Fore.BLACK}Start {start.strftime("%d-%b-%Y")} | End {end.strftime("%d-%b-%Y")} | {days:,} Days | {days/365:,.2f} Years{Style.RESET_ALL}')
        print(f'\n{Back.MAGENTA}Annualized {round(all_realized / days * 365):,}{Back.RESET}')

def runOptionTrades():
    print(f'{Fore.GREEN}[ Option Trades ]{Style.RESET_ALL}')

    option_trades = parser.trades_group()
    option_trades = parser.group_with_column_name(option_trades, 'Asset Category', ASSET_CATEGORY_OPTIONS)
    option_trades = parser.group_with_column_name(option_trades, 'DataDiscriminator', 'Order')

    option_header = option_trades[0]

    stock_trades = parser.trades_group()
    stock_trades = parser.group_with_column_name(stock_trades, 'Asset Category', ASSET_CATEGORY_STOCKS)
    stock_trades = parser.group_with_column_name(stock_trades, 'DataDiscriminator', 'Order')

    stock_header = stock_trades[0]
    stock_trades = list(filter(lambda x: x[stock_header.index('Symbol')] in parser.option_trades_symbols(), stock_trades[1:]))
    stock_trades = list(filter(lambda x: x[stock_header.index('Code')] in ['A;O','A;C','C'], stock_trades[1:]))
    stock_trades = sorted(stock_trades, key=lambda x: x[stock_header.index('Code')], reverse=False)

    print(tabulate(option_trades[1:], headers=option_header))
    print()
    print(tabulate(stock_trades, headers=stock_header))

argparser = argparse.ArgumentParser(description='Interactive Brokers summary report')
argparser.add_argument("-data", help="data path", required=True)
# argparser.add_argument("-p", "--period", choices=['all', 'ytd'], help="reporting period")
argparser.add_argument("-s", "--symbol", help="stock symbol")
argparser.add_argument("--trades", action='store_true', help="show trades")
argparser.add_argument("--options", action='store_true', help="options positions")
argparser.add_argument("--json", action='store_true', help="json format")
args = argparser.parse_args()

parser = IBCSVParser()

directory = args.data + '/'
# directory = f'{utils.file_path(__file__)}/data/'

files = []
for r, d, f in os.walk(directory  ):
    for file in f:
        if file.endswith('.csv'):
            files.append(file)
files.sort()

if(len(files) == 0):
    print(f'{Fore.RED}no csv files found')
    exit()

parser.clear()

# ytd
if not args.symbol:
    parser.add(directory + files[-1])

    if not args.json:
        displayDot()
        displayTradingPeriod()
        displayPerformance(ALL_ASSET_CATEGORIES, [], ['Realized Total', 'Unrealized Total'])
        displayCashReport()
        displayBondCouponPayments()
        displayDot()
    # else:
    #     print('json')

# all
if args.symbol:
    for file in files:
        parser.add(directory + file)

    if not args.json:
        displayDot()
        displayTrades(args.symbol, args.trades)
        displayDot()
    # else:
    #     print('json')

def header_split(data):
    return [data.pop(0), data]

def get_positions(category):
    # get options positions from csv file
    open_positions = parser.open_positions_group()
    pos = parser.group_with_column_name(open_positions, 'Header', 'Data')
    pos = parser.group_with_column_name(pos, 'Asset Category', category)

    # separate header from data
    header, pos = header_split(pos)

    # drop columns
    drop = ['Open Positions','Header','DataDiscriminator','Asset Category','Currency','Mult','Cost Price','Close Price','Value','Unrealized P/L','Code']

    return drop_columns(drop, header, pos)

def get_performance():
    # get performance from csv file to get symbol current price
    performance = parser.performance_summary_group()
    performance = parser.group_with_column_name(performance, 'Header', 'Data')
    # performance = parser.group_with_column_name(performance, 'Asset Category', 'Equity and Index Options')
    performance_header, performance_data = header_split(performance)

    # remove rows that have prior quantity & prior price instead of currenty quantity & current price
    performance_data = list(filter(lambda x: x[performance_header.index('Current Quantity')] != '0', performance_data))

    # drop columns
    drop = ['Mark-to-Market Performance Summary','Header','Asset Category','Prior Quantity','Prior Price','Mark-to-Market P/L Position','Mark-to-Market P/L Transaction','Mark-to-Market P/L Commissions', 'Mark-to-Market P/L Other','Mark-to-Market P/L Total', 'Code']
    performance_header, performance_data = drop_columns(drop, performance_header, performance_data)

    return performance_header, performance_data

def symbol_price(position_row):
    performance_header, performance_data = get_performance()

    # position values
    symbol, quantity, price = position_row

    # performance indices
    pidx_symbol = performance_header.index('Symbol')
    pidx_qty = performance_header.index('Current Quantity')

    # filter performance data to find performance row
    performance_row = list(filter(lambda x: (x[pidx_symbol] == symbol and x[pidx_qty] == quantity), performance_data))

    # price
    price = performance_row[0][performance_header.index('Current Price')] if len(performance_row) else 0

    # add to position
    position_row.append(price)

    return position_row

def add_performance(header, positions):
    positions = [symbol_price(row) for row in positions]

    # add price key to header
    header.append('Price')

    return header, positions

def split_option_symbol(header, options):
    # Symbol to Symbol, Expiration, Strike, Right
    header[1:1] = ['Expiration','Strike','Right']

    # PLTR 21JAN22 27.0 P to PLTR, 21JAN22, 27.0, P
    def option_row(row):
        row[0:1] = row[0].split()
        return row

    options = map(option_row, options)

    return header, options

def json_transformations(header, positions):
    # lowercase header
    header = [x.lower() for x in header]

    # key changes
    header = [key.replace('cost basis', 'basis') for key in header]

    # add header keys to every option row
    positions = [dict(zip(header, row)) for row in positions]

    return positions

if args.json:
    if args.options:
        data = {}

        o_header, options = get_positions('Equity and Index Options')
        o_header, options = add_performance(o_header, options)
        o_header, options = split_option_symbol(o_header, options)
        options = json_transformations(o_header, options)
        data['options'] = options

        s_header, stocks = get_positions('Stocks')
        stocks = json_transformations(s_header, stocks)

        data['stocks'] = stocks

        data['period'] = parser.report_period()
        data['generated'] = parser.report_generated()

        print(json.dumps(data))