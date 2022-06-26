import numpy as np
from scipy import signal
from Forex.Market import LiveTicks
import matplotlib.pyplot as plt
import MetaTrader5 as mt5
import pandas as pd

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
import pytz

# establish connection to MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# set time zone to UTC
timezone = pytz.timezone("Etc/UTC")
# create 'datetime' objects in UTC time zone to avoid the implementation of a local time zone offset


from datetime import datetime, timedelta

utc_from = datetime(2022, 6, 24, 22,1, tzinfo=timezone)
print(utc_from - timedelta(minutes=5))
# datetime.utcnow() > utc_from
time_from = utc_from - timedelta(minutes=300)

# request 100 000 EURUSD ticks starting from 10.01.2019 in UTC time zone
# ticks = mt5.copy_ticks_range("XAUUSD", utc_from, utc_to, mt5.COPY_TICKS_ALL)
ticks =mt5.copy_ticks_from("XAUUSD", time_from, 100, mt5.COPY_TICKS_ALL)
ticks_frame = pd.DataFrame(ticks)
# convert time in seconds into the datetime format
ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
print(ticks_frame.tail(10))
import matplotlib.pyplot as plt
print(any(ticks_frame.ask.diff()[-10:]) >=1)
plt.plot(ticks_frame.ask, c='r')
plt.plot(ticks_frame.bid, c='b')

plt.show()
