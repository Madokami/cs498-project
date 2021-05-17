import datetime as dt
import threading
import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
import analysis_utils as autils
import logging
import configparser
import os
import pytz
import time
from datetime import timedelta
from alpaca_trade_api.rest import TimeFrame

def init_alpaca_api():
    try:
        config = configparser.ConfigParser()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config.read(dir_path + '/config.ini')
        user_profile = config['profile']
        api_key_id = user_profile.get("apca_api_key_id")
        api_secret_key = user_profile.get("apca_api_secret_key")
        api_endpoint = user_profile.get("apca_api_endpoint")
        api = tradeapi.REST(api_key_id, api_secret_key, api_endpoint, 'v2')
        api.cancel_all_orders() # cancel or orders for a clean start
        return api
    except Exception as e:
        log_warning(e)
        return None

# calculate RSI based on historic data
# returns the latest RSI value
def calculate_rsi(api, barset, symbol, rsi_window):
    # Calculate the RSI (relative strength index)
    up_prices=[]
    down_prices=[]
    for i in range(0, len(barset)):
        if i == 0:
            up_prices.append(0)
            down_prices.append(0)
        else:
            diff = barset[i] - barset[i-1]
            if diff > 0:
                up_prices.append(diff)
                down_prices.append(0)
            else:
                up_prices.append(0)
                down_prices.append(diff)
    # Get latest trade price and count it as the last gain or loss
    # TODO: add exception handling here in case this fails
    try:
        last_trade = api.get_last_trade(symbol)
    except Exception as e:
        log_warning(e)
        return -1
    diff = last_trade.price - barset[-1]
    if diff > 0:
        up_prices.append(diff)
        down_prices.append(0)
    else:
        up_prices.append(0)
        down_prices.append(diff)

    rsi = []
    for i in range(0, len(up_prices)):
        if i < rsi_window:
            rsi.append(100)
        else:
            sum_gain = np.sum(up_prices[i - rsi_window + 1:i + 1])
            sum_loss = np.sum(down_prices[i - rsi_window + 1:i + 1])
            avg_gain = sum_gain/rsi_window
            avg_loss = abs(sum_loss/rsi_window)
            if avg_loss == 0:
                rsi.append(100)
            else:
                rsi.append(100-100/(1 + avg_gain/avg_loss))
    return rsi[-1]

# Gets hourly bars for a symbol. The end_date is inclusive.
def get_stock_historic_data_hourly_helper(api, symbol, start_date, end_date):
    try:
        return api.get_bars(symbol, TimeFrame.Hour, start_date, end_date, limit=10000).df["open"]
    except Exception as e:
        log_warning(e)
        return None

# Get historical stock data for the most recent num_days.
def get_stock_historic_data_hourly(api, symbol, num_days):
    timezone = pytz.timezone('America/Los_Angeles')
    # Get the current time, 15minutes, and 1 hour ago
    time_now = dt.datetime.now(tz=timezone)
    end_date = time_now - dt.timedelta(minutes=15)
    start_date = time_now - dt.timedelta(days=num_days)

    barset = get_stock_historic_data_hourly_helper(api, symbol, start_date.isoformat(), end_date.isoformat())
    if barset is None:
        # If the operation failed, try again but with an even earlier end_date
        end_date = time_now - dt.timedelta(hours=1)
        return get_stock_historic_data_hourly_helper(api, symbol, start_date.isoformat(), end_date.isoformat())
    return barset

# Check whether the market is open
def check_market_open(api):
    try:
        return api.get_clock().is_open
    except Exception as e:
        log_warning(e)
        return False

# Get current cash available for trading
def get_cash(api):
    try:
        return float(api.get_account().cash)
    except Exception as e:
        log_warning(e)
        return 0

# Sell all of the given stock at the current market price.
def sell_stock(api, symbol):
    try:
        positions = api.list_positions()
        contains_symbol = False
        for pos in positions:
            if pos.symbol == symbol:
                contains_symbol = True
                break
        if not contains_symbol:
            return
        api.close_position(symbol)
        log_message("Successfully sold all shares of " + str(symbol))
    except Exception as e:
        log_warning(e)

# Buy a stock at current market price with all available cash.
def buy_stock(api, symbol):
    cash = get_cash(api)
    if cash <= 0:
        return
    try:
        last_trade = api.get_last_trade(symbol)
        num_stocks = int(cash/last_trade.price) - 1 # buy 1 less stock to make sure the order goes through
        if num_stocks <= 0:
            return
        api.submit_order(symbol, num_stocks, "buy", "market", "day")
        log_message("Successfully bought " + str(num_stocks) + " shares of " + str(symbol))
    except Exception as e:
        log_warning(e)

def init_logger():
    today = dt.datetime.now()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_name = dir_path + "/logs/" + today.strftime("%Y-%m-%d") + ".log"
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=file_name, level=logging.INFO, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

# Logging level for fatal failures that cause the program to exit
def log_error(e):
    print("Fatal: ", e)
    logging.error(e)

# Logging level for API call failures
def log_warning(e):
    print("Warning: ", e)
    logging.error(e)

# Logging level for informative messages
def log_message(message):
    print("Message: ", message)
    logging.info(message)

# TODO: add logging and email notification to help with debugging.
def main():
    init_logger()
    log_message("Starting program...")
    api = init_alpaca_api()
    if api is None:
        log_error("Failed to create API surface, shutting down...")
        return
    
    if not check_market_open(api):
        log_error("Market is not open, shutting down...") # This program expects to be setup to run during market hours
        return
    
    symbol_primary = "QQQ" # Primarily do analysis and try to time buys on this stock.
    symbol_secondary = "SPY" # Always hold this stock after selling the primary stock to not miss out on market gains.
    rsi_window = 14 # the window size used to calculate RSI.
    end_date = dt.datetime.now()
    start_date = end_date - timedelta(days=7)
    barset = get_stock_historic_data_hourly(api, symbol_primary, 7) # barset should be a pandas Series
    if barset is None:
        log_error("Failed to get historical stock data, shutting down...")
        return
    
    if len(barset) < rsi_window:
        log_error("Insufficient historical data for RSI calculation, shutting down...")
        return
    
    latest_rsi = calculate_rsi(api, barset, symbol_primary, rsi_window)
    log_message("Latest RSI=" + str(latest_rsi))
    if latest_rsi < 0 or latest_rsi > 100:
        log_error("Unexpected RSI=" + str(latest_rsi) + ", shutting down...")
        return
    
    if latest_rsi <= 30:
        # Sell symbol_secondary to buy symbol_primary
        sell_stock(api, symbol_secondary)
        time.sleep(10) # wait a bit to make sure everything is sold
        buy_stock(api, symbol_primary)
    elif latest_rsi >= 95:
        # Sell symbol_primary to buy symbol_secondary
        sell_stock(api, symbol_primary)
        time.sleep(10) # wait a bit to make sure everything is sold
        buy_stock(api, symbol_secondary)
        
    log_message("Execution completed, shutting down...")

if __name__ == "__main__":
    main()
