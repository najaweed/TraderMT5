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


class Candle:
    def __init__(self,
                 df_ticks,
                 ):
        self.df = df_ticks
        self.zones = [('00:00', '07:00'), ('07:15', '13:45'), ('14:00', '23:45'), ]

    def gen_tick_bar(self):
        df = []
        daily_dfs = [group[1] for group in self.df.groupby(self.df.index.date)]
        for daily_df in daily_dfs:
            df_zones = self._split_markets(daily_df)
            # for df_zone in df_zones:
            #     df.append(self._gen_ohlc(df_zone))
            df.append(self._gen_ohlc(df_zones[0]))
            df.append(self._gen_ohlc(df_zones[1]))
            df.append(self._gen_ohlc(df_zones[2]))

        return pd.concat(df)

    def _split_markets(self, daily_df):
        df_zones = []
        for zone in self.zones:
            df_zones.append(daily_df.between_time(*zone))

        return df_zones

    def _gen_ohlc(self, df):
        df_rate = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        if len(df) != 0:
            df_rate.loc[df.index[-1], 'open'] = df.open[0]
            df_rate.loc[df.index[-1], 'high'] = df.high.max()
            df_rate.loc[df.index[-1], 'low'] = df.low.min()
            df_rate.loc[df.index[-1], 'close'] = df.close[-1]
            df_rate.loc[df.index[-1], 'volume'] = sum(df.tick_volume)
        return df_rate


# df = Candle(rates).gen_tick_bar()
# img = df.iloc[100:106, 0:4].to_numpy(dtype=float)
# print(img)
#
# # plt.figure(1)
# # plt.imshow(img.T, interpolation='none')
#
# img -= img[-1, -1]
# print(img)
#
# img = img.max() - img
#
# img /= img.max() - img.min()
# print(img)
# plt.figure(22)
#
# plt.imshow(img.T, interpolation='none')
# plt.show()
# r1m = Candle(rates).gen_tick_bar()
# print(r1m.tail(30))
# rates.to_csv("C:\\Users\\z\\Desktop\\rates_m1.csv")
# import finplot as fplt
#
# fplt.foreground = '#eef'
# fplt.background = '#0a081b'
# candle_bull_color = '#26a69a'
# candle_bear_color = '#ef5350'
# fplt.odd_plot_background = '#0a081b'
# ax = fplt.create_plot('Things move', rows=1, init_zoom_periods=2 * 60, maximize=True)
# fplt.candlestick_ochl(r1m[['open', 'close', 'high', 'low']].dropna(), ax=ax)
# #fplt.add_rect(1, 100, color='#26a69a', interactive=False, ax=ax)
#
# fplt.show(qt_exec=True)
