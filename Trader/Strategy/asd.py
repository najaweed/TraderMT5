import numpy as np
import pandas as pd
from Forex.Market import LiveTicks
import MetaTrader5 as mt5
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

live_config = {'symbol': 'XAUUSD',
               'window': 60 * 24 * 60, }
live_trader = LiveTicks(config=live_config)
df_rates = live_trader.get_rates(mt5.TIMEFRAME_M2)

# set time zone to UTC
import pytz

timezone = pytz.timezone("Etc/UTC")
# create 'datetime' objects in UTC time zone to avoid the implementation of a local time zone offset
utc_from = datetime(2022, 1, 10, tzinfo=timezone)
utc_to = datetime(2022, 7, 7, tzinfo=timezone)
# get bars from USDJPY M5 within the interval of 2020.01.10 00:00 - 2020.01.11 13:00 in UTC time zone
rates = mt5.copy_rates_range("GBPJPY", mt5.TIMEFRAME_M5, utc_from, utc_to)
rates = pd.DataFrame(rates)
rates['time'] = pd.to_datetime(rates['time'], unit='s')
rates = rates.set_index('time')
#pd.set_option('display.max_columns', 500)  # number of columns to be displayed
#pd.set_option('display.width', 1500)  # max table width to display
print(rates.tail(30))
#plt.plot(rates.close[:1000])
#plt.show()

def add_stl_plot(fig, res, legend):
    """Add 3 plots from a second STL fit"""
    axs = fig.get_axes()
    comps = ["trend", "seasonal", "resid"]
    for ax, comp in zip(axs[1:], comps):
        series = getattr(res, comp)
        if comp == "resid":
            ax.plot(series, marker="o", linestyle="none")
        else:
            ax.plot(series)
            if comp == "trend":
                ax.legend(legend, frameon=False)


from statsmodels.tsa.seasonal import STL

close = rates.close[:1001]
# stl = STL(close[:1000],period=200,seasonal=11)
#
# res = stl.fit()
# trend = res.trend
# de_close = close - trend
# plt.figure(22)
# plt.plot(close)
# plt.plot(trend)
#
# plt.figure(11)
# plt.plot(de_close)
# plt.show()
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.forecasting.stl import STLForecast

stlf = STLForecast(close, ARIMA, model_kwargs=dict(order=(1, 0, 1), trend="t"),period=100,seasonal=11)
stlf_res = stlf.fit()

forecast = stlf_res.forecast(24)
plt.plot(close)
plt.plot(rates.close[1000:1000+24])
plt.plot(forecast)
plt.show()