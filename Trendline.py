import numpy as np
import pandas as pd
import requests
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
from scipy.signal import argrelextrema
import ssl
from urllib import request
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()  #apscheculer
matplotlib.use('agg')

WEBHOOK_URL2 ="https://discord.com/api/webhooks/891602942698868766/rfQvyRL2H0AkiI8G9M4eLCqhZoh2frs6dV2iYt58dJIdInwcQ8bbNf1nSNAS0rEa6Aam"

def Hisse_Temel_Veriler():
    base_url = "https://api.binance.com/api/v3/exchangeInfo"

    try:
        response = requests.get(base_url)
        data = response.json()
        if "symbols" in data:
            Hisseler= [pair["symbol"] for pair in data["symbols"] if pair["quoteAsset"] == "USDT" and "LEVERAGED" not in pair["permissions"]]
            return Hisseler
        else:
            return []
    except Exception as e:
        return []


def Stock_Prices(coin_symbol, interval="15m", limit=1000):
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": coin_symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        response = requests.get(base_url, params=params)
        data1 = response.json()
        # print(data1)
        data = pd.DataFrame(data1, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
        data["timestamp"] = pd.to_datetime(data["timestamp"], unit="ms")
        # print(data)
        return data
    except Exception as e:
        return pd.DataFrame()


def Trend_Channel(df):

    df['close'] = df.close.astype(float)
    # print(df)
    best_period = None
    best_r_value = 0
    periods = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
    for period in periods:
        close_data = df['close'].tail(period)
        # print(close_data)
        x = np.arange(len(close_data))
        # print(x)
        slope, intercept, r_value, _, _ = stats.linregress(x, close_data)
        # print(r_value)
        if abs(r_value) > abs(best_r_value):
            best_r_value = r_value
            best_period = period
    # print(best_period, best_r_value)
    return best_period, best_r_value

def Plot_Trendlines(Hisse,data,best_period,rval=0.85):
    data['close'] = data.close.astype(float)
    # print(data['close'])
    plt.close()

    close_data = data['close'].tail(best_period)
    # print(close_data)
    x_best_period = np.arange(len(close_data))
    # print(x_best_period)
    slope_best_period, intercept_best_period, r_value_best_period, _, _ = stats.linregress(x_best_period, close_data)
    trendline=slope_best_period * x_best_period + intercept_best_period
    upper_channel = (slope_best_period * x_best_period + intercept_best_period) + (trendline.std() * 1.1)
    lower_channel = (slope_best_period * x_best_period + intercept_best_period) - (trendline.std() * 1.1)

    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['close'], label='Kapanış Fiyatı')
    plt.plot(data.index[-best_period:], trendline, 'g-', label=f'Trend Çizgisi (R={r_value_best_period:.2f})')
    plt.fill_between(data.index[-best_period:], upper_channel, trendline, color='lightgreen', alpha=0.3, label='Üst Kanal')
    plt.fill_between(data.index[-best_period:], trendline, lower_channel, color='lightcoral', alpha=0.3, label='Alt Kanal')
    plt.title(str(Hisse)+' Kapanış Fiyatı ve Trend Çizgisi')
    plt.xlabel('Tarih Endeksi')
    plt.ylabel('Kapanış Fiyatı')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    upper_diff = upper_channel - close_data
    lower_diff = close_data - lower_channel
    last_upper_diff = upper_diff.iloc[-1]
    last_lower_diff = lower_diff.iloc[-1]

    # print("r_value_best_period")
    # print(r_value_best_period)
    # print("rval")
    # print(rval)
    # print("last_lower_diff")
    # print(last_lower_diff)

    if abs(r_value_best_period) > rval and (last_upper_diff < 0):
        print(str(Hisse)+' Yazdırıldı.')
        print('Trend Yukarı yönlü kırılmış.')
        print('Hesaplanan R Değeri:'+str(abs(r_value_best_period)))
        print('Hesaplanan Fark:'+str(last_upper_diff))
        plt.savefig(f'{Hisse}_Yukarı_Kırılım.png', bbox_inches='tight', dpi=200)
        # message = f"```diff\n+ {Hisse}\n```"
        message = f"```diff\n+ **{Hisse}** için Trend Yukarı yönlü kırılmış\n```"
        payload = {
        "username": "alertbot",
        "content": message
        }
        requests.post(WEBHOOK_URL2, json=payload)

    if abs(r_value_best_period) > rval and (last_lower_diff < 0):
        print(str(Hisse)+' Yazdırıldı.')
        print('Trend Aşağı yönlü kırılmış')
        print('Hesaplanan R Değeri:'+str(abs(r_value_best_period)))
        print('Hesaplanan Fark:'+str(last_lower_diff))
        plt.savefig(f'{Hisse}_Aşağı_Kırılım.png', bbox_inches='tight', dpi=200)
        # message = f"```diff\n- {Hisse}\n ```"
        message = f"```diff\n- **{Hisse}** için Trend aşağı yönlü kırılmış\n ```"
        payload = {
        "username": "alertbot",
        "content": message
        }
        requests.post(WEBHOOK_URL2, json=payload)
    return

def scan():
    Hisseler=Hisse_Temel_Veriler()
    for i in range(0,len(Hisseler)):
        print(Hisseler[i])
        try:
            data=Stock_Prices(Hisseler[i], interval="15m", limit=1000)
            best_period, best_r_value = Trend_Channel(data)
            Plot_Trendlines(Hisseler[i],data,best_period)
        except:
            pass
# scan()

# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=5, second=10)
# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=10, second=10)
sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=15, second=10)
# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=20, second=10)
sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=30, second=10)
# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=35, second=10)
# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=40, second=10)
sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=45, second=10)
# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=50, second=10)
# sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=55, second=10)
sched.add_job( scan, 'cron', day_of_week='mon-sun', minute=0, second=10)

sched.start()

