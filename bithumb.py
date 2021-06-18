import time
import pybithumb
import datetime
import telegram
import pandas as pd
import numpy as np
import schedule

key = '52e0b79c17b52a0501cbcf00137560d4'
secret = 'c274d68f9e2e236ab71478fdbe9b0cb3'
bithumb = pybithumb.Bithumb(key, secret)

def get_ror(k=0.5):
    df = pybithumb.get_ohlcv("BTC")
    df = df.tail(5)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0032
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)
    ror = df['ror'].cumprod()[-2]
    return ror

df1 = pd.DataFrame(columns = None)
for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k)
    df1 = df1.append(pd.DataFrame([[k,ror]]))
            
maxbenefit = max(df1.loc[:,1])
maxks = df1.loc[df1[1] == maxbenefit, 0]
maxk = maxks.iloc[0]

# 목표가를 target으로 추출
def get_target_price(ticker):
    df = pybithumb.get_ohlcv(ticker)
    yesterday = df.iloc[-2] # 어제 종가 추출

    today_open = yesterday['close'] # 어제 종가 = 오늘 시가
    yesterday_high = yesterday['high']
    yesterday_low = yesterday['low']
    target = today_open + (yesterday_high - yesterday_low) * maxk
    return target

def buy_crypto_currency(ticker):
    krw = bithumb.get_balance(ticker)[2]
    orderbook = pybithumb.get_orderbook(ticker)
    sell_price = orderbook['asks'][0]['price']   
    unit = krw/float(sell_price)
    bithumb.buy_market_order(ticker, unit)

def sell_crypto_currency(ticker):
    unit = bithumb.get_balance(ticker)[0]
    bithumb.sell_market_order(ticker, unit) 

def get_yesterday_ma5(ticker):
    df = pybithumb.get_ohlcv(ticker)
    close = df['close']
    ma = close.rolling(5).mean()
    return ma[-2]

now = datetime.datetime.now() # 현재 시간 추출
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1) # 현재시간에 1일을 더한것을 더한값 추출
ma5 = get_yesterday_ma5("BTC")
target_price = get_target_price("BTC")

while True:
    bot = telegram.Bot(token='921370813:AAEH296WqKKLrtkKGjwRiLvTQaUz5Sfx8ms')
    def job():
        bot.send_message(chat_id = 1096591010, text='activating')
    schedule.every(1).hours.do(job)
    try:
        now = datetime.datetime.now() # 현재 시간 추출
        if mid < now < mid + datetime.delta(seconds=10): # 현재시간이 다음날 같은 시간전 10초일때

            # 임의의 자정마다 최대k값 재 선정
            df1 = pd.DataFrame(columns = None)
            for k in np.arange(0.1, 1.0, 0.1):
                ror = get_ror(k)
                df1 = df1.append(pd.DataFrame([[k,ror]]))
            
            maxbenefit = max(df1.loc[:,1])
            maxks = df1.loc[df1[1] == maxbenefit, 0]
            maxk = maxks.iloc[0]

            target_price = get_target_price("BTC")
            mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1) # 현재시간에 1일을 더한것을 더한값 추출
            ma5 = get_yesterday_ma5("BTC")
            sell_crypto_currency("BTC")

            bot = telegram.Bot(token='921370813:AAEH296WqKKLrtkKGjwRiLvTQaUz5Sfx8ms')
            bot.send_message(chat_id = 1096591010, text= ' '+ maxk +', ' + krw )
            print(df1)
            print(maxk)
    
        current_price = pybithumb.get_current_price("BTC")        
        if (current_price > target_price) and (current_price > ma5):
            buy_crypto_currency("BTC")        
    except:
        print("에러 발생")        
    time.sleep(1)
