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

    def matrix_dynamic_distance(self, df: dict, normal_dist: bool = True):
        df = self._normalizer(df)
        distance = self._matrix_distance(df,normal_dist)
        return distance

    def _normalizer(self, df: dict):
        normal_df = {}
        if self.config['normal_method'] == 'z_score':
            for sym, rate in df.items():
                normal_df[f'{sym}'] = zscore(rate)
        return normal_df

    def _matrix_distance(self, df: dict, normal_dist: bool = True):
        dist = np.zeros((len(df), len(df)))
        lead_lag = np.zeros((len(df), len(df)))

        for i, (sym_i, rate_i) in enumerate(df.items()):
            for j, (sym_j, rate_j) in enumerate(df.items()):
                if sym_i != sym_j:
                    if isinstance(rate_j, np.ndarray):
                        dist[i, j], lead_lag[i, j] = self.__dynamic_time_warping(rate_i, rate_j)

                    elif 'open' in rate_j.columns:
                        dist[i, j], lead_lag[i, j] = self.__dynamic_time_warping(rate_i.close.to_numpy(),
                                                                                 rate_j.close.to_numpy())
                    elif 'ask' in rate_j.columns:
                        dist[i, j], lead_lag[i, j] = self.__dynamic_time_warping(rate_i.ask.to_numpy(),
                                                                                 rate_j.ask.to_numpy())
        dist = self.__normalize_distance(dist) if normal_dist else dist
        return dist, self.__lead_lag(lead_lag)

    def __dynamic_time_warping(self, x_1: np.ndarray, x_2: np.ndarray):
        distance = 0
        lead_lag = 0
        if self.config['distance'] == 'euclidean':
            radi = 5  # max(len(x_1), len(x_2))
            distance, warp_path = fastdtw(x_1, x_2, radius=radi, dist=euclidean)

            xx = sum([w[0] for w in warp_path])
            yy = sum([w[1] for w in warp_path])
            lead_lag = 1 - (yy / xx)

        return distance, lead_lag

    def __lead_lag(self, lead_lag):
        lead_lag_x = np.zeros_like(lead_lag)

        for i in range(len(lead_lag)):
            for j in range(len(lead_lag)):
                if i > j:
                    ll = (lead_lag[i, j] - lead_lag[j, i]) / 2
                    if ll > 0:
                        lead_lag_x[i, j] = ll
                    elif ll < 0:
                        lead_lag_x[j, i] = -ll
        return lead_lag_x

    def __normalize_distance(self, distance):

        max = np.max(distance)
        distance[distance == 0] = np.inf
        min = np.min(distance)
        distance -= min
        distance /= (max - min)
        distance += 0.05
        distance[distance == np.inf] = 0

        return distance


# ## TEST CLASS
# # from LiveRate import ForexMarket
# #
# # currenciesx = ['USD', 'EUR', 'GBP', 'JPY', ]  # 'CHF',]# 'CAD', 'AUD', 'NZD']
# # # print(ForexMarket(currenciesx).get_all_rates())
# # # print(ForexMarket(currenciesx).get_all_df())
# # fx = ForexMarket(currenciesx)
# # ticks = fx.get_all_df(shift=60)
#
#
#
# ##TEST
# ticks = {}
# sym = ['a','b','c']
# t = np.linspace(0, 1000, 100)
# shift = [0 , 0, 1.5*np.pi]
# frq = [1,1,1]
# for i in range(len(sym)):
#     ticks[f'{sym[i]}'] = np.sin(2*np.pi*frq[i]*t + shift[i])
#
#
# default_config = {'normal_method': 'z_score',
#                   'distance': 'euclidean'}
# dist, lead_laga = DynamicDistance(default_config).matrix_dynamic_distance(ticks, False)
# print(dist)
# print(lead_laga)
# for i in range(len(lead_laga)):
#     for j in range(len(lead_laga)):
#         if lead_laga[i,j] >0:
#             print(i,j)
# import networkx as nx
# import matplotlib.pyplot as plt
#
# G = nx.DiGraph(directed=True)
# for i in range(len(lead_laga)):
#     for j in range(len(lead_laga)):
#         if i != j :
#             if lead_laga[i,j] > 0:
#                 G.add_edge(i,j)
#
# G = nx.DiGraph(G,directed=True)
# nx.draw(G,
#         pos=nx.circular_layout(G),
#         with_labels=True,
#         node_size=1000,
#         node_color='y',
#         )  # use spring layout
# plt.draw()
# plt.show()
# #
