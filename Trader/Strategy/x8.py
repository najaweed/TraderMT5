import numpy as np
import pandas as pd
from Forex.Market import LiveTicks
import MetaTrader5 as mt5

live_config = {'symbol': 'XAUUSD',
               'window': 60 * 24 * 60, }
live_trader = LiveTicks(config=live_config)
df_rates = live_trader.get_rates(mt5.TIMEFRAME_M1)

df = df_rates


class Candle:
    def __init__(self,
                 df_ticks,
                 ):
        self.df = df_ticks
        self.zones = [('00:00', '07:00'), ('07:00', '13:45'), ('13:45', '23:59'), ]

    def gen_tick_bar(self):
        df = []
        daily_dfs = [group[1] for group in self.df.groupby(self.df.index.date)]
        for daily_df in daily_dfs:
            df_zones = self._split_markets(daily_df)
            for df_zone in df_zones:
                df.append(self._gen_ohlc(df_zone))
        return pd.concat(df)

    def _split_markets(self, daily_df):
        df_zones = []
        for zone in self.zones:

            df_zones.append(daily_df.between_time(*zone))

        return df_zones


    def _gen_ohlc(self, df):
        df_rate = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        if len(df) !=0:
            df_rate.loc[df.index[-1], 'open'] = df.open[0]
            df_rate.loc[df.index[-1], 'high'] = df.high.max()
            df_rate.loc[df.index[-1], 'low'] = df.low.min()
            df_rate.loc[df.index[-1], 'close'] = df.close[-1]
            df_rate.loc[df.index[-1], 'volume'] = sum(df.tick_volume)
        return df_rate


r1m=Candle(df_rates).gen_tick_bar()
import finplot as fplt
fplt.foreground = '#eef'
fplt.background = '#0a081b'
candle_bull_color = '#26a69a'
candle_bear_color = '#ef5350'
fplt.odd_plot_background = '#0a081b'
ax = fplt.create_plot('Things move', rows=1, init_zoom_periods=2 * 60, maximize=True)
fplt.candlestick_ochl(r1m[['open', 'close', 'high', 'low']].dropna(), ax=ax)
fplt.show(qt_exec=True)
