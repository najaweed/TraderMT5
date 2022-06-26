from Trader.Strategy.abcStrategy import Strategy
from scipy.signal import argrelextrema
import numpy as np
import pandas as pd
from Trader.Strategy.Trends import Trend


class Scalper(Strategy):
    def __init__(self,
                 step_df,
                 step_df_2,
                 ):
        self.df = step_df[:-1]
        self.df_2 = step_df_2[:-1]
        self.sl = None
        self.tp = None
        self.dynamic_lines()

    def _buy_zone(self):
        pass

    def _sell_zone(self):
        pass

    def _estimate_sl(self):
        return self.sl

    def _estimate_tp(self):
        return self.tp

    def _estimate_volume(self):
        pass

    def dynamic_lines(self):
        Trend(self.df_2).get_trends(time_frame=5)
        pass

    def static_lines(self, alpha=5, beta_1=0.2, beta_2=0.3):
        static_line = int(alpha * round(float(self.df.open[-1]) / alpha))
        # print(self.df.iloc[-1, :4] - static_line)
        if abs(static_line - self.df.open[-1]) >= beta_1 and abs(static_line - self.df.close[-1]) >= beta_1:
            if abs(self.df.low[-1] - static_line) <= beta_2:
                print('static buy signal')
                return 'Buy'
            elif abs(static_line - self.df.high[-1]) <= beta_2:
                print('static sell signal')
                return 'Sell'
        else:
            return False

    def candle_pattern(self, alpha_1=2, beta_min=0.1, beta_max=2.0, alpha_4=0.01):
        diff = self.df.close[-1] - self.df.open[-1]
        high_shadow = self.df.high[-1] - max(self.df.close[-1], self.df.open[-1])
        low_shadow = min(self.df.close[-1], self.df.open[-1]) - self.df.low[-1]
        # print(self.df.iloc[-1, :])
        # print(f'diff ={diff}  , low shadow = {low_shadow} , high shadow = {high_shadow}')
        if beta_max >= diff >= beta_min and abs(alpha_1 * diff) <= abs(low_shadow) and abs(high_shadow) <= alpha_4:
            print('candle buy signal')
            return 'Buy'
        elif -beta_max <= diff <= -beta_min and abs(alpha_1 * diff) <= abs(high_shadow) and abs(low_shadow) <= alpha_4:
            print('candle sell signal')
            return 'Sell'
        else:
            return False
