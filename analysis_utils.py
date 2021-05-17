import numpy as np

# Simulate trading by using MACD and RSI signals to buy and sell an equity that has higher votality. When the stock is sold,
# always buy the baseline equity with lower votality to make sure the money is being used.
# Parameters:
# ticker: arraylike structure with price of the equity per day
# baseline_ticker: arraylike structure with price of the baseline equity per day
# macd_surplus: array of MACD minus the signal line
# rsi: array of the calculated related strength index (0, 100]. The higher the more overbought.
# min_days_hold: wait at least this many days after buying to sell
def calculate_returns_macd_rsi(ticker, baseline_ticker, macd_surplus, rsi, min_days_hold):
    # MACD with RSI with baseline stock
    money_start = 10000.0
    money = money_start
    stock = 0
    stock_baseline = 0
    prev = 0
    cur = 0
    turning_point = 0

    # data to create graph
    account_value = ticker.copy(deep=True)

    # buy the baseline stock
    num_stock = money/baseline_ticker[0]
    stock_baseline = num_stock
    money = 0
    last_buy_day = 0
    last_index = len(ticker) - 1

    for i in range (0, len(ticker)):
        cur = macd_surplus[i]
        stock_price = ticker[i]
        baseline_price = baseline_ticker[i]
        if (cur >= turning_point and prev <= turning_point and rsi[i] < 60):
            # first sell any baseline stocks
            # print("Sell SPY", stock_baseline, " at ", baseline_price)
            money += stock_baseline * baseline_price
            stock_baseline = 0

            # buy the actual target stock
            num_stock = int(money/stock_price)
            if num_stock >= 1:
                stock += num_stock
                money -= stock_price * num_stock
                last_buy_day = i
                #print("Buy ", num_stock, " at ", stock_price)
        elif (cur < turning_point and prev >= turning_point and rsi[i] > 40):
            if i >= last_buy_day + min_days_hold:
                num_stock = stock
                money += num_stock * stock_price
                stock -= num_stock
                # print("Sell ", num_stock, " at ", stock_price)

                # buy the baseline stock
                num_stock = money/baseline_price
                stock_baseline += num_stock
                #print("Buy SPY", num_stock, " at ", baseline_price)
                money = 0
        prev = cur
        account_value[i] = money + stock*stock_price + stock_baseline*baseline_price
    money = account_value[-1]
    gain = money/money_start
    predicted_return = {'gain': gain, 'days': len(ticker)}
    return predicted_return

def calculate_returns_macd_only(ticker, baseline_ticker, macd_surplus, rsi, min_days_hold):
    money_start = 10000.0
    money = money_start
    stock = 0
    prev = 0
    cur = 0
    base_load = 0.6
    turning_point = 0
    last_buy_day = 0
    for i in range (0, len(ticker)):
        cur = macd_surplus[i]
        if (cur >= turning_point and prev <= turning_point):
            # Buy
            num_stock = int(money/ticker[i])
            if num_stock >= 1:
                stock += num_stock
                money -= ticker[i] * num_stock
                last_buy_day = i
                #print("Buy ", num_stock, " at ", ticker[i])
        elif (cur < turning_point and prev >= turning_point):
            # sell
            if i >= last_buy_day + min_days_hold:
                num_stock = int((1 - base_load) * stock)
                money += num_stock * ticker[i]
                stock -= num_stock
                #print("Sell ", num_stock, " at ", ticker[i])
        prev = cur
    money += stock * ticker[-1]
    gain = money/money_start
    predicted_return = {'gain': gain, 'days': len(ticker)}
    return predicted_return

def calculate_returns_macd_rsi_simple(ticker, baseline_ticker, macd_surplus, rsi, min_days_hold):
    # MACD with RSI
    money_start = 10000.0
    money = money_start
    stock = 0
    prev = 0
    cur = 0
    base_load = 0.6
    turning_point = 0
    last_buy_day = 0
    account_value = ticker.copy(deep=True)

    for i in range (0, len(ticker)):
        cur = macd_surplus[i]
        stock_price = ticker[i]
        if (cur >= turning_point and prev <= turning_point and rsi[i] < 60):
            # Buy
            num_stock = int(money/stock_price)
            if num_stock >= 1:
                stock += num_stock
                money -= stock_price * num_stock
                last_buy_day = i
                #print("Buy ", num_stock, " at ", stock_price)
        elif (cur < turning_point and prev >= turning_point or rsi[i] > 70):
            # sell
            if i >= last_buy_day + min_days_hold:
                num_stock = int((1 - base_load) * stock)
                money += num_stock * stock_price
                stock -= num_stock
                #print("Sell ", num_stock, " at ", stock_price)
        prev = cur
        account_value[i] = money + stock*stock_price

    money += stock * ticker[-1]
    gain = money/money_start
    predicted_return = {'gain': gain, 'days': len(ticker)}
    return predicted_return

def calculate_returns_rsi_only(ticker, ticker_short, rsi):
    # trade with RSI only
    money_start = 10000.0
    money = money_start
    stock = 0
    stock_short = 0
    oversold = 30
    overbought = 95
    total_deal = 0
    success_deal = 0
    account_value = ticker.copy(deep=True)

    stock_price = ticker[0]
    last_bought_at = stock_price
    num_stock = int(money/stock_price)
    if num_stock >= 1:
        stock += num_stock
        money -= stock_price * num_stock
        print("Buy ", num_stock, " at ", stock_price)
    for i in range(0, 14):
        stock_price = ticker[i]
        account_value[i] = stock * stock_price
    
    for i in range (14, len(ticker)):
        cur = rsi[i]
        stock_price = ticker[i]
        stock_price_short = ticker_short[i]
        if (cur <= oversold):
            # Sell shorts
            if stock_short > 0:
                print("Sell SPY ", stock_short, " at ", stock_price_short)
                money += stock_short * stock_price_short
                stock_short = 0
                
            # Buy long
            num_stock = int(money/stock_price)
            if num_stock >= 1:
                stock += num_stock
                money -= stock_price * num_stock
                last_bought_at = stock_price
                print("Buy QQQ ", num_stock, " at ", stock_price)
        elif (cur >= overbought):
            # sell long
            if stock > 0:
                print("Sell QQQ ", stock, " at ", stock_price)
                money += stock * stock_price
                stock = 0
                total_deal += 1
                if last_bought_at < stock_price:
                    success_deal += 1
            
            # buy short
            num_stock = int(money/stock_price_short)
            if num_stock >= 1:
                stock_short += num_stock
                money -= stock_price_short * num_stock
                print("Buy SPY ", num_stock, " at ", stock_price_short)
        account_value[i] = money + stock*stock_price + stock_short*stock_price_short
            
    money += stock * ticker[-1] + stock_short * ticker_short[-1]
    gain = money/money_start
    if total_deal == 0:
        success_rate = 0
    else:
        success_rate = success_deal/total_deal
    predicted_return = {'gain': gain, 'samples': len(ticker), "success_rate": success_rate, "account_value": account_value}
    return predicted_return

def calculate_rsi(ticker):
    # Calculate the RSI (relative strength index)
    up_prices=[]
    down_prices=[]
    for i in range(0, len(ticker)):
        if i == 0:
            up_prices.append(0)
            down_prices.append(0)
        else:
            diff = ticker[i] - ticker[i-1]
            if diff > 0:
                up_prices.append(diff)
                down_prices.append(0)
            else:
                up_prices.append(0)
                down_prices.append(diff)

    avg_gain_list=[]
    avg_loss_list=[]
    rsi = ticker.copy(deep=True)
    rsi_window = 14
    x = 0
    while x < len(up_prices):
        if x < rsi_window:
            avg_gain_list.append(0)
            avg_loss_list.append(0)
            rsi[x] = 100
        else:
            sum_gain = np.sum(up_prices[x - rsi_window + 1:x + 1])
            sum_loss = np.sum(down_prices[x - rsi_window + 1:x + 1])
            avg_gain = sum_gain/rsi_window
            avg_loss = abs(sum_loss/rsi_window)
            avg_gain_list.append(avg_gain)
            avg_loss_list.append(avg_loss)
            if avg_loss == 0:
                rsi[x] = 100
            else:
                rsi[x] = (100-100/(1 + avg_gain/avg_loss))
        x += 1
    return rsi

def calculate_macd_surplus(ticker, symbol):
    # Calculation for MACD
    exp1 = ticker.ewm(span=12, adjust=False).mean()
    exp2 = ticker.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    exp3 = macd.ewm(span=9, adjust=False).mean()
    macd_surplus = macd - exp3
    return macd_surplus