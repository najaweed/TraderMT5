import numpy as np

# Normalizer
from scipy.stats import zscore

# Computation Dynamic time Warping packages
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw


class DynamicDistance:
    def __init__(self,
                 config: dict,
                 ):
        self.config = config

    def matrix_dynamic_distance(self, df: dict):
        df = self._normalizer(df)
        distance = self._matrix_distance(df)
        return distance

    def _normalizer(self, df: dict):
        normal_df = {}
        if self.config['normal_method'] == 'z_score':
            for sym, rate in df.items():
                normal_df[f'{sym}'] = zscore(rate)
        return normal_df

    def _matrix_distance(self, df: dict):
        dist = np.zeros((len(df), len(df)))
        for i, (sym_i, rate_i) in enumerate(df.items()):
            for j, (sym_j, rate_j) in enumerate(df.items()):
                if sym_i != sym_j:
                    dist[i, j] = self.__dynamic_time_warping(rate_i.close.to_numpy(), rate_j.close.to_numpy())
                    dist[j, i] = dist[i, j]
        return dist

    def __dynamic_time_warping(self, x_1: np.ndarray, x_2: np.ndarray):
        distance = 0
        if self.config['distance'] == 'euclidean':
            distance, warp_path = fastdtw(x_1, x_2, radius=max(len(x_1), len(x_2)), dist=euclidean)
        return distance


# # TEST CLASS
# from LiveRate import ForexMarket
# currenciesx = ['USD', 'EUR', 'GBP', ]#'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
# #print(ForexMarket(currenciesx).get_all_rates())
# #print(ForexMarket(currenciesx).get_all_df())
# ticks = ForexMarket(currenciesx).get_all_df(shift=60)
# #print(ticks)
# default_config = {'normal_method': 'z_score',
#                   'distance': 'euclidean'}
# print(DynamicDistance(default_config).matrix_dynamic_distance(ticks))
