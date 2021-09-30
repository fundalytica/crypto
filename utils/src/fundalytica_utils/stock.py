import re
from datetime import datetime

import pandas as pd
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, nearest_workday, USMartinLutherKingJr, USPresidentsDay, USMemorialDay, USLaborDay, USThanksgivingDay, GoodFriday

def valid_symbol(symbol):
    STOCK_SYMBOL_PATTERN = "[A-Z]{1,4}((\.){1}[A|B]{1}){0,1}$"
    pattern = re.compile(STOCK_SYMBOL_PATTERN)
    match = pattern.match(symbol)
    return match is not None

def USTradingCalendar():
    class USTradingCalendar(AbstractHolidayCalendar):
        rules = [
            Holiday('NewYearsDay', month=1, day=1, observance=nearest_workday),
            Holiday('USIndependenceDay', month=7, day=4, observance=nearest_workday),
            Holiday('Christmas', month=12, day=25, observance=nearest_workday),
            USMartinLutherKingJr,
            USPresidentsDay,
            GoodFriday,
            USMemorialDay,
            USLaborDay,
            USThanksgivingDay
        ]
    return USTradingCalendar()

def isUSMarketOpen(nyc_date):
    # not a weekend
    is_not_weekend = nyc_date.weekday() not in [5,6]

    # nyc_date = datetime(1971, 2, 15) # test holiday 1971-02-15
    holidays = USTradingCalendar().holidays(nyc_date, nyc_date)
    is_not_holiday = len(holidays) == 0

    # trading hours 09:30 - 16:00
    trading_start = datetime(nyc_date.year, nyc_date.month, nyc_date.day, 9, 0, 0, tzinfo=nyc_date.tzinfo)
    trading_end = datetime(nyc_date.year, nyc_date.month, nyc_date.day, 16, 30, 0, tzinfo=nyc_date.tzinfo)
    in_trading_hours = nyc_date <= trading_end and nyc_date >= trading_start

    return is_not_weekend and is_not_holiday and in_trading_hours