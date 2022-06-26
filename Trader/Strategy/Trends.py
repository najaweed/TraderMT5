import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


class Trend:
    def __init__(self,
                 df_rates,
                 ):
        self.df = df_rates
        # self.df = self._gen_tick_bar('1min')

    def get_trends(self, time_frame=5, tf='min'):
        trend_points = {}

        # for i in time_frame:
        i = time_frame
        df = self.df

        arg_high = argrelextrema(df.high.to_numpy(), np.greater, order=2)[0]
        arg_low = argrelextrema(-df.low.to_numpy(), np.greater, order=2)[0]
        print(arg_low, arg_high)
        if len(arg_high) >= 2:
            points = self._get_resistance(df.high, arg_high, i, tf)
            print(points)
            trend_points[f'{i},{tf},resistance'] = points
        if len(arg_low) >= 2:
            points = self._get_supports(df.low, arg_low, i, tf)
            trend_points[f'{i},{tf},support'] = points
            print(points)

        return trend_points

    def _gen_tick_bar(self, time_frame: str):
        df = self.df.open.resample(time_frame).first().to_frame()
        df['close'] = self.df.close.resample(time_frame).last()
        df['high'] = self.df.high.resample(time_frame).max()
        df['low'] = self.df.low.resample(time_frame).min()
        return df

    def _get_resistance(self, df, arg_df, i, tf):

        temp_index_1 = df.index[arg_df[-1]]
        range_price_1 = self.df.high[temp_index_1:(temp_index_1 + pd.Timedelta(i, unit=tf))]
        price_1 = df[arg_df[-1]]
        index_1 = range_price_1[range_price_1 == price_1].index[0]
        print(range_price_1)
        temp_index_2 = df.index[arg_df[-2]]
        range_price_2 = self.df.high[temp_index_2:(temp_index_2 + pd.Timedelta(i, unit=tf))]
        price_2 = df[arg_df[-2]]
        index_2 = range_price_2[range_price_2 == price_2].index[0]
        print(range_price_2)

        alpha = (df[arg_df[-1]] - df[arg_df[-2]]) / abs((index_1 - index_2).total_seconds() / 60)
        t_end = abs((self.df.close.index[-1] - index_1).total_seconds() / 60)

        predict_price = df[arg_df[-1]] + alpha * t_end
        index_last = self.df.close.index[-1]

        points = [[(index_2, price_2), (index_1, price_1)],
                  [(index_1, price_1), (index_last, predict_price)],
                  [alpha, t_end]
                  ]
        return points

    def _get_supports(self, df, arg_df, i, tf):

        temp_index_1 = df.index[arg_df[-1]]
        range_price_1 = self.df.low[temp_index_1:(temp_index_1 + pd.Timedelta(i, unit=tf))]
        price_1 = df[arg_df[-1]]
        index_1 = range_price_1[range_price_1 == price_1].index[0]

        temp_index_2 = df.index[arg_df[-2]]
        range_price_2 = self.df.low[temp_index_2:(temp_index_2 + pd.Timedelta(i, unit=tf))]
        price_2 = df[arg_df[-2]]
        index_2 = range_price_2[range_price_2 == price_2].index[0]

        alpha = (df[arg_df[-1]] - df[arg_df[-2]]) / abs((index_1 - index_2).total_seconds() / 60)
        t_end = abs((self.df.close.index[-1] - index_1).total_seconds() / 60)

        predict_price = df[arg_df[-1]] + alpha * t_end
        index_last = self.df.close.index[-1]

        points = [[(index_2, price_2), (index_1, price_1)],
                  [(index_1, price_1), (index_last, predict_price)],
                  [alpha, t_end]
                  ]
        return points
