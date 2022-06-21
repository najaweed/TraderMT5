from Trader.Strategy.abcStrategy import Strategy


class Scalper(Strategy):
    def __init__(self,
                 step_df,
                 ):
        self.df = step_df
        self.sl = None
        self.tp = None
        self.candle_pattern()
        breakpoint()

    def _buy_zone(self):
        pass

    def _sell_zone(self):
        pass

    def _estimate_st(self):
        pass

    def _estimate_tp(self):
        pass

    def _estimate_volume(self):
        pass

    def candle_pattern(self, alpha_1=2, alpha_2=4, beta_1=0.2, beta_2=0.2):
        diff = self.df.close[-1] - self.df.open[-1]
        high_shadow = self.df.high[-1] - self.df.close[-1] if diff >= 0 else self.df.high[-1] - self.df.close[-1]
        low_shadow = self.df.open[-1] - self.df.low[-1] if diff >= 0 else self.df.close[-1] - self.df.low[-1]

        if diff >= 0 and abs(alpha_1 * diff) <= low_shadow and abs(diff) >= alpha_2 * high_shadow:
            if abs(self.df.open[-1] - int(5 * round(float(self.df.open[-1]) / 5))) >= beta_1:
                if abs(self.df.low[-1] - int(5 * round(float(self.df.open[-1]) / 5))) <= beta_2:
                    return 'Buy'
        elif diff <= 0 and abs(alpha_1 * diff) <= high_shadow and abs(diff) >= alpha_2 * low_shadow:
            if abs(self.df.close[-1] - int(5 * round(float(self.df.close[-1]) / 5))) >= beta_1:
                if abs(self.df.high[-1] - int(5 * round(float(self.df.close[-1]) / 5))) <= beta_2:
                    return 'Sell'
        else:
            return False
