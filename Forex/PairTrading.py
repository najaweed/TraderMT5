from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz

pd.set_option('display.max_columns', 200)
pd.set_option('display.max_rows', 100)


def get_live_tick(symbol, time_shift=200):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    timezone = pytz.timezone("Etc/GMT-3")
    utc_from = datetime(2022, 7, 25,hour=1, tzinfo=timezone)
    utc_to = datetime(2022, 7, 25,hour=16, tzinfo=timezone)
    # request AUDUSD ticks within 11.01.2020 - 11.01.2020
    #ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_ALL)
    #print(ticks)
    ticks = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, utc_from, utc_to)
    print("Ticks received:", len(ticks))

    # time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)
    #
    # ticks = mt5.copy_ticks_from(symbol, time_from, 100000, mt5.COPY_TICKS_ALL)
    # print(ticks)
    # breakpoint()
    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    # last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame  # .loc[last_ticks_index:, :]


df1 = get_live_tick('EURUSD_i')
df2 = get_live_tick('GBPUSD_i')
df3 = get_live_tick('EURGBP_i')



plt.figure(111)
plt.plot(df1.high)

plt.figure(222)
plt.plot(df2.low)

plt.figure(333)
plt.plot(df3.close)


#plt.figure(1122)
x = df1.high / df2.low

plt.plot(x)

plt.figure(4444)
plt.plot( x / df3.close   )

plt.show()
