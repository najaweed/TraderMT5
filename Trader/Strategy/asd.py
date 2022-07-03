import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import argrelextrema
import numpy as np
# Generate a noisy AR(1) sample
from Forex.Market import LiveTicks
import MetaTrader5 as mt5

np.random.seed(0)
rs = np.random.randn(200)
xs = [0]
for r in rs:
    xs.append(xs[-1] * 0.9 + r)


def ext(df_rates):
    df = df_rates
    for n in reversed(range(5, 100, 5)):
        # n = 500#int(len(df)/50)
        # Find local peaks
        print(n)
        df['min'] = df.iloc[argrelextrema(df.low.values, np.less_equal,
                                          order=n)[0]]['low']
        df['max'] = df.iloc[argrelextrema(df.high.values, np.greater_equal,
                                          order=n)[0]]['volume']

        # Plot results
        plt.scatter(df.index, df['min'], c='r')
        plt.scatter(df.index, df['max'], c='g')
        plt.plot(df.index, df['volume'])
        #plt.plot(df.index, df['high'])

        plt.show()


live_config = {'symbol': 'XAUUSD',
               'window': 8 * 60, }
live_trader = LiveTicks(config=live_config)
print()
df_rates = live_trader.get_rates(mt5.TIMEFRAME_M1)

ext(df_rates)
