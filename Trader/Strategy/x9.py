from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz
import time
import matplotlib.pyplot as plt

timezone = pytz.timezone("Etc/GMT-3")

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

pd.set_option('display.max_columns', 500)  # number of columns to be displayed
pd.set_option('display.width', 1500)  # max table width to display


def get_live_tick(symbol, time_shift=20):
    time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)

    utc_from = datetime(2020, 1, 10, tzinfo=timezone)
    utc_to = datetime(2020, 1, 11, tzinfo=timezone)
    # request AUDUSD ticks within 11.01.2020 - 11.01.2020
    # ticks = mt5.copy_ticks_range(symbol, time_from, datetime.now(tz=timezone), mt5.COPY_TICKS_ALL)

    ticks = mt5.copy_ticks_from(symbol, time_from, 100000, mt5.COPY_TICKS_ALL)
    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame.loc[last_ticks_index:, :]




def ewma(data, window):
    alpha = 2 / (window + 1.0)
    alpha_rev = 1 - alpha

    scale = 1 / alpha_rev
    n = data.shape[0]

    r = np.arange(n)
    scale_arr = scale ** r
    offset = data[0] * alpha_rev ** (r + 1)
    pw0 = alpha * alpha_rev ** (n - 1)

    mult = data * pw0 * scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums * scale_arr[::-1]
    return out


def _rsi(df, window=40):
    diff_ask = df.ask.diff().dropna()
    diff_bid = df.bid.diff().dropna()
    up_bid = diff_bid.clip(lower=0).to_numpy()
    down_ask = diff_ask.clip(upper=0).to_numpy()

    ewm_ask = ewma(down_ask[down_ask < 0], window)
    ewm_bid = ewma(up_bid[up_bid > 0], window)
    # plt.plot(-ewm_ask)
    # plt.plot(ewm_bid)
    # plt.show()
    lead_len = len(ewm_bid) if len(ewm_bid) < len(ewm_ask) else len(ewm_ask)

    rsi = ewm_bid[-lead_len:] / (-1*ewm_ask[-lead_len:])
    return 100 - (100 / (1 + rsi))
def low_pass_filter(xs, alpha=0.8):
    # low_cut = band[0] / (len(xs) / 2)
    from scipy import signal

    xs = np.concatenate((xs, xs[::-1]))
    sig = signal.butter(N=4, Wn=alpha, btype='lowpass')
    b = sig[0]
    a = sig[1]
    y1 = signal.filtfilt(b, a, xs)

    xs = y1[:int(len(xs) / 2)]
    return xs


while True:
    ticks = get_live_tick('GBPJPY_i',120)
    print(ticks)
    plt.figure(12)

    plt.plot(ticks.ask.to_numpy())
    plt.plot(low_pass_filter(ticks.ask.to_numpy(),alpha=0.01))
    #plt.plot(ewma(ticks.ask.to_numpy(),20))
    x_1 = low_pass_filter(ticks.ask.to_numpy(),alpha=0.5)
    x_2 = low_pass_filter(ticks.ask.to_numpy(),alpha=0.0005)
    plt.plot(low_pass_filter(ticks.ask.to_numpy(),alpha=0.0005))
    plt.figure(2)
    plt.plot(x_2-x_1)


    plt.show()

# print(get_live_tick('AUDNZD'))
# ticks = get_live_tick('AUDNZD')
# plt.figure(1)
# plt.plot(ticks.ask.to_numpy(), c='r')
# plt.plot(ticks.bid.to_numpy(), c='b')
# plt.figure(2)
# plt.plot(ticks.ask.to_numpy() - ticks.bid.to_numpy())
#
# plt.show()
