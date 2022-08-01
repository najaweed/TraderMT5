import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


class PriceLevel:
    def __init__(self,
                 df: pd.DataFrame,
                 ):
        self.df = df

    def price_levels(self):
        resistance = self._find_resistance()
        support = self._find_support()
        return {'support': support,
                'resistance': resistance}

    def point_for_plot(self):
        resistance = self._find_resistance()
        support = self._find_support()
        start_datetime = self.df.index[0]
        end_datetime = self.df.index[-1]

        points = {'support':[(start_datetime,support['price']),(end_datetime,support['price'])],
                  'resistance':[(start_datetime,resistance['price']),(end_datetime,resistance['price'])]}
        return points


    def _find_resistance(self,):

        df_high = self.df['high'].to_numpy()
        high_peaks = []
        for i in range(3, int(len(df_high)/1)):
            peaks = argrelextrema(df_high, np.greater_equal, order=i)[0]
            high_peaks.append(df_high[peaks])

        # flatten list
        high_peaks = [num for elem in high_peaks for num in elem]
        # get population of each price
        high_peaks = {i: high_peaks.count(i) for i in high_peaks}
        avg = np.average(list(high_peaks.keys()), weights=list(high_peaks.values()))
        variance = np.average((np.array(list(high_peaks.keys())) - avg) ** 2, weights=list(high_peaks.values()))
        std = np.sqrt(variance)
        return {'price': avg, 'std': std}

    def _find_support(self,):
        df_low = self.df['low'].to_numpy()
        low_peaks = []
        for i in range(3, int(len(df_low)/1)):
            peaks = argrelextrema(df_low, np.less_equal, order=i)[0]
            low_peaks.append(df_low[peaks])

        # flatten list
        low_peaks = [num for elem in low_peaks for num in elem]
        # get population of each price
        low_peaks = {i: low_peaks.count(i) for i in low_peaks}
        avg = np.average(list(low_peaks.keys()), weights=list(low_peaks.values()))
        variance = np.average((np.array(list(low_peaks.keys())) - avg) ** 2, weights=list(low_peaks.values()))
        std = np.sqrt(variance)
        return {'price': avg, 'std': std}


# # TEST CLASS
# from LiveRate import HistoricalCandle
# xticks = HistoricalCandle('EURGBP_i').get_last_year()
# price_lvl = PriceLevel(xticks).price_levels()
# print(price_lvl)

# # # PLOT SHIT
# # from matplotlib import pyplot as plt
# # plt.plot(xticks['high'].to_numpy())
# # plt.plot(xticks['low'].to_numpy())
# # for key, val in price_lvl.items():
# #     print(key, val)
# #     plt.axhline(val['price'])
# #     plt.fill_between(range(len(xticks['low'])),
# #                      val['price'] * np.ones_like(xticks['low']) - val['std'] / 3,
# #                      val['price'] * np.ones_like(xticks['low']) + val['std'] / 3,
# #                      alpha=1,
# #                      edgecolor='#3F7F4C',
# #                      facecolor='#7EFF99',
# #                      linewidth=0)
# # plt.show()
