import analysis_utils as autils
from datetime import timedelta
import pandas as pd
import pandas_datareader as pdr
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import configparser
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame

def main():
    # Load stock data
    config = configparser.ConfigParser()
    config.read('config.ini')
    user_profile = config['profile']
    api_key_id = user_profile.get("apca_api_key_id")
    api_secret_key = user_profile.get("apca_api_secret_key")
    api_endpoint = user_profile.get("apca_api_endpoint")
    api = tradeapi.REST(api_key_id, api_secret_key, api_endpoint, 'v2')
    symbol = "QQQ"
    window_days = 365
    first_date = dt.datetime(2016, 1, 1)
    cur_date = first_date
    last_valid_date = dt.datetime.now() - timedelta(days=1) - timedelta(days=window_days)
    gains_rsi_only = []
    hold_gains = []
    hold_gains_2 = []
    while(cur_date < last_valid_date):
        print("Analyzing date=", str(cur_date))
        end_date = cur_date + timedelta(days=window_days)
        barset = api.get_bars(symbol, TimeFrame.Hour, cur_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), limit=10000).df["close"]
        barset_short = api.get_bars("SPY", TimeFrame.Hour, cur_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), limit=10000).df["close"]
        print(len(barset))
        print(len(barset_short))
        rsi = autils.calculate_rsi(barset)
        result = autils.calculate_returns_rsi_only(barset, barset_short, rsi)
        print("Success rate=", result['success_rate'])
        gains_rsi_only.append(result['gain'])
        hold_gains.append(barset[-1]/barset[0])
        hold_gains_2.append(barset_short[-1]/barset_short[0])
        cur_date = cur_date + timedelta(days=window_days)
    
    df_rsi_only  = pd.DataFrame(gains_rsi_only);
    df_hold = pd.DataFrame(hold_gains)
    print("\nProjected yearly gains for RSI algorithm:")
    print(df_rsi_only.describe())
    print("\nYearly hold gains for QQQ:")
    print(df_hold.describe())
    df_hold = pd.DataFrame(hold_gains_2)
    print("\nYearly hold gains for SPY")
    print(df_hold.describe())
    
    '''
    num_trade_day_year = 253 # number of trading days in a year
    start_date = dt.datetime(2010, 1, 1)
    end_date = dt.datetime.now()
    symbol = "QQQ"
    ticker = pdr.get_data_yahoo(symbol, start_date, end_date)['Adj Close']
    baseline_ticker = pdr.get_data_yahoo("SPY", start_date, end_date)['Adj Close']
    rsi = autils.calculate_rsi(ticker)
    macd_surplus = autils.calculate_macd_surplus(ticker, symbol)
    start = 0
    iterations = 0
    gains_macd_rsi = []
    gains_macd_only = []
    gains_macd_rsi_simple = []
    gains_rsi_buy = []
    gains_rsi_only = []
    hold_gains = []
    baseline_hold_gains = []
    step_size = 5
    while start < len(ticker) - num_trade_day_year:
        print("Analyzing iterations=", iterations)
        end = start + num_trade_day_year
        ticker_year = ticker[start:end]
        baseline_ticker_year = baseline_ticker[start:end]
        hold_gains.append(ticker[end]/ticker[start])
        baseline_hold_gains.append(baseline_ticker[end]/baseline_ticker[start])
        
        result = autils.calculate_returns_macd_rsi(ticker_year, baseline_ticker_year, macd_surplus, rsi, 0)
        gains_macd_rsi.append(result['gain'])
        result = autils.calculate_returns_macd_only(ticker_year, baseline_ticker_year, macd_surplus, rsi, 35)
        gains_macd_only.append(result['gain'])
        result = autils.calculate_returns_macd_rsi_simple(ticker_year, baseline_ticker_year, macd_surplus, rsi, 0)
        gains_macd_rsi_simple.append(result['gain'])
        result = autils.calculate_returns_rsi_only(ticker_year, rsi, 0)
        gains_rsi_only.append(result['gain'])
        iterations += 1
        start += step_size
    
    for i in range(0, len(rsi) - num_trade_day_year):
        if rsi[i] < 40 and rsi[i] > 30:
            end = i + num_trade_day_year
            gains_rsi_buy.append(ticker[end]/ticker[i])
    
    df_macd_rsi = pd.DataFrame(gains_macd_rsi)
    df_macd_only = pd.DataFrame(gains_macd_only)
    df_macd_rsi_simple = pd.DataFrame(gains_macd_rsi_simple)
    df_rsi_buy = pd.DataFrame(gains_rsi_buy)
    df_rsi_only  = pd.DataFrame(gains_rsi_only);
    df_hold = pd.DataFrame(hold_gains)
    df_baseline_hold = pd.DataFrame(baseline_hold_gains)
    print("Projected gains gains_macd_rsi")
    print(df_macd_rsi.describe())
    print("\nProjected gains gains_macd_only")
    print(df_macd_only.describe())
    print("\nProjected gains gains_macd_rsi_simple")
    print(df_macd_rsi_simple.describe())
    print("\nProjected gains gains_rsi_buy")
    print(df_rsi_buy.describe())
    print("\nProjected gains rsi only")
    print(df_rsi_only.describe())
    print("\nHold gain")
    print(df_hold.describe())
    print("\nBaseline hold gain")
    print(df_baseline_hold.describe())
    '''

if __name__ == "__main__":
    main()

'''
                0
count  367.000000
mean     1.323809
std      0.399760
min      0.459188
25%      1.060349
50%      1.316410
75%      1.520784
max      3.630184

Hold gain
                0
count  367.000000
mean     1.576905
std      0.515948
min      0.713885
25%      1.162228
50%      1.556916
75%      1.918390
max      4.399898

Baseline hold gain
                0
count  367.000000
mean     1.137602
std      0.089148
min      0.829249
25%      1.068163
50%      1.148959
75%      1.198894
max      1.389914
'''