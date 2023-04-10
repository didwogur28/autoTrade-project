import traceback

import pyupbit
import time
import datetime
import pandas as pd
import keyboard

def get_target_price(ticker, interval, k):  # 변동성 돌파 전략으로 매수 목표가 정하기
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker, interval):  # 시작 시간 조회
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=1)
    start_time = df.index[0]
    return start_time


def get_current_price(ticker):  # 현재 가격 가져오기

    return pyupbit.get_orderbook(ticker=ticker)['orderbook_units'][0]['ask_price']


def get_balance(coinName):  # 잔고 조회
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coinName:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0


def get_buy_average(currency):  # 매수평균가
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == currency:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0


def get_trade_time(ticker):  # 최근 거래 채결 날짜 가져오기
    df = pd.DataFrame(upbit.get_order(ticker, state="done"))
    trade_done = df.iloc[0]["created_at"]
    trade_done_time = datetime.datetime.strptime(trade_done[:-6], "%Y-%m-%dT%H:%M:%S")
    return trade_done_time


##########################################################################################################

# 로그인
access = '[ACCESS_KEY]'
secret = '[SECRET_KEY]'

upbit = pyupbit.Upbit(access, secret)
print("Login OK")

# 총 매수 할 원화, 분할 매수 비율
total = 7000000
rate30 = 0.3
rate40 = 0.4
rate_minus = 0.95

# 시간 간격
intervalDay = "day"
interval240 = "minute240"
interval60 = "minute60"
interval1 = "minute1"

print("자동매매 프로그램을 시작합니다.")
anwser = input("매매 할 코인을 입력해주세요 : ")

# ticker, coinName, currency, k
ticker = "KRW-" + anwser
coinName = anwser
currency = "KRW"
k = 0.12

targetPriceCnt = 0
start_chk = "Y"

buy_average = 0
current_price = 0

# 자동 매매 무한 반복
while True:

    while start_chk == "Y":

        time.sleep(10)

        # 시간 설정
        start_time = get_start_time(ticker, interval60)
        now = datetime.datetime.now()
        # end_time = start_time + datetime.timedelta(days=1) - datetime.timedelta(seconds=5)
        end_time = start_time + datetime.timedelta(minutes=60) - datetime.timedelta(seconds=5)

        # 매매 시작
        if start_time < now < end_time:

            if targetPriceCnt == 0:
                target_price = round(get_target_price(ticker, intervalDay, k), 2)

            print("Start: %s" % (start_time))
            print("End: %s" % (end_time))
            print("Target price: %f" % (target_price))

            targetPriceCnt = 1
            i = 0
            printCnt = 0

            while i < 3:
                now = datetime.datetime.now()
                current_price = round(get_current_price(ticker), 2)
                current_count = get_balance("KRW")
                avgBuyPrice = round(upbit.get_avg_buy_price(coinName), 2)
                time.sleep(0.5)

                if printCnt % 60 == 0:
                    print("====================")
                    print("코인 매수 가격: %f" % (target_price))
                    print("현재 코인 가격: %f" % (current_price))
                    print("현재 잔고: %d" % (current_count))
                    print("코인 매수 평균가: %f" % (avgBuyPrice))
                    print("====================")

                # 매수 1차
                if i == 0 and (target_price - 0.1) <= current_price < (target_price + 0.05):
                    # if i == 0 and target_price == current_price:

                    print("1차 매수 시작")

                    try:
                        if current_count > total * rate30:
                            upbit.buy_market_order(ticker, total * rate30)
                            time.sleep(1)
                            buy_average = get_buy_average(currency)
                            print("%dst Buy OK" % (i))

                        i += 1

                    except Exception as e:
                        trace_back = traceback.format_exc()
                        message = str(e) + "\n" + str(trace_back)
                        print(message)

                # 매수 2차
                if i == 1 and current_price < buy_average * rate_minus:

                    print("2차 매수 시작")

                    try:
                        if current_count > total * rate30:
                            upbit.buy_market_order(ticker, total * rate30)
                            time.sleep(1)
                            buy_average = get_buy_average(currency)
                            print("%dst Buy OK" % (i))

                        i += 1

                    except Exception as e:
                        trace_back = traceback.format_exc()
                        message = str(e) + "\n" + str(trace_back)
                        print(message)

                # 매수 3차
                if i == 2 and current_price < buy_average * rate_minus:

                    print("3차 매수 시작")

                    try:
                        if current_count > total * rate30:
                            upbit.buy_market_order(ticker, total * rate40)
                            time.sleep(1)
                            buy_average = get_buy_average(currency)
                            print("%dst Buy OK" % (i))

                        i += 1

                    except Exception as e:
                        trace_back = traceback.format_exc()
                        message = str(e) + "\n" + str(trace_back)
                        print(message)

                if i != 0 and round((avgBuyPrice / current_price), 2) <= 0.98:

                    print("2프로 이상 상승 판매")
                    upbit.sell_market_order(ticker, coin)
                    time.sleep(1)
                    break

                if now > end_time:

                    if avgBuyPrice < current_price:

                        print("시간 끝 코인 매도")

                        coin = get_balance(coinName)
                        upbit.sell_market_order(ticker, coin)
                        time.sleep(1)
                        print("Sell OK")

                    break

                printCnt += 1

                if keyboard.is_pressed('n'):
                    start_chk = "N"
                    break

            avgBuyPrice = upbit.get_avg_buy_price(coinName)
            print("코인 매수 평균가: %f" % (avgBuyPrice))

            if i != 0 and round((avgBuyPrice / current_price), 2) <= 0.98:

                print("2프로 이상 상승 판매")

                coin = get_balance(coinName)
                upbit.sell_market_order(ticker, coin)
                time.sleep(1)
                break

        elif now > end_time:

            avgBuyPrice = upbit.get_avg_buy_price(coinName)
            print("코인 매수 평균가: %f" % (avgBuyPrice))

            if avgBuyPrice < current_price:

                print("시간 끝 코인 매도")

                coin = get_balance(coinName)
                upbit.sell_market_order(ticker, coin)
                time.sleep(1)
                print("Sell OK")

    if start_chk == "N":
        print("\n")
        anwser = input("매매 할 코인을 입력해주세요 : ")

        ticker = "KRW-" + anwser
        coinName = anwser

        start_chk = "Y"
        targetPriceCnt = 0

    time.sleep(1)
