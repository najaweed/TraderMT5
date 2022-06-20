from Trader.Strategy.abcStrategy import Strategy


class SimpleStrategy(Strategy):
    def __init__(self,
                 step_df,
                 ):
        self.df = step_df

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
