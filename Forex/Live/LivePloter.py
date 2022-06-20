from Forex.Market import LiveTicks
import time
from Forex.TradeChannels import Plotter
import MetaTrader5 as mt5

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
class LivePlotter:
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

    def __init__(self,
                 config,
                 ):
        self.live = LiveTicks(config)
        self.plotter = config['plotter']

        self.last_tick = self.live.get_rates().index[-1]

    def _check_new_tick(self):
        tick = self.live.get_rates().index[-1]
        if tick > self.last_tick:
            self.last_tick = tick
            return True
        else:
            return False

    def main(self):
        while True:

            if self._check_new_tick():
                print(self.last_tick)
                df = self.live.get_rates()
                self.plotter.plot_channels(df)
                # PLOT
            #
            else:
                pass

            time.sleep(5)


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation

def plt_candlestick(df: pd.DataFrame):
    open = df.open
    close = df.close
    high = df.high
    low = df.low
    time_index = df.index

    color = ["green" if close_price > open_price else "red" for close_price, open_price in
             zip(df.close.to_numpy(), df.open.to_numpy())]
    plt.bar(x=time_index,
            height=np.abs(open - close),
            bottom=np.min((open, close), axis=0),
            width=5e-4,
            color=color,
            # alpha=1/time_frame_min,
            )
    plt.bar(x=time_index,
            height=high - low,
            bottom=low,
            width=1e-4,
            color=color,
            # alpha=1/time_frame_min,
            )


trader_config = {
    "symbol": 'XAUUSD',
    "window": 360 * 6 * 6,
    "digit": 1e2,
    "plotter": Plotter([]),
}
#
# live = LiveTicks(trader_config).get_rates()
# def plt_update(i):
#
#     plt_candlestick(LiveTicks(trader_config).get_rates())
# anit = FuncAnimation(plt.gcf(),plt_update,interval=5000)
# plt.grid(alpha=0.5)
# plt.show()
#c
live_plot = LivePlotter(trader_config)
live_plot.main()
