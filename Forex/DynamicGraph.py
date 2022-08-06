# # TEST CLASS
import networkx as nx

from DynamicDistance import DynamicDistance
# TEST CLASS
from LiveRate import ForexMarket

# Dendrogram (Single Linkage)
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as sch
import scipy.spatial.distance as dist
import numpy as np
import MetaTrader5 as mt5

#
# while True:
#     currenciesx = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', ]  # 'CAD',]# 'AUD',]# 'NZD']
#     # print(ForexMarket(currenciesx).get_all_rates())
#     # print(ForexMarket(currenciesx).get_all_df())
#     fx = ForexMarket(currenciesx)
#
#     ticks = fx.get_all_df(shift=70, time_frame=mt5.TIMEFRAME_M1)
#     # ticks = fx.get_all_tick_df(time_shift_min=15)
#
#     default_config = {'normal_method': 'z_score',
#                       'distance': 'euclidean'}
#     distxy, _ = DynamicDistance(default_config).matrix_dynamic_distance(ticks)
#     print(distxy)
#     plt.figure(1211)
#
#     link_distance = dist.squareform(distxy)
#     # link_distance -= np.min(link_distance)
#     # link_distance /= (np.max(link_distance) - np.min(link_distance))
#     # link_distance += 0.05
#
#     Z = sch.linkage(link_distance, method='single')
#     labels = [f'{sym[:3]} / {sym[3:6]}' for sym in fx.symbols]
#     den = sch.dendrogram(Z, labels=labels)
#     plt.title('Dendrogram (Single Linkage) for the clustering of the dataset')
#     plt.xlabel('Data Points Number')
#     plt.ylabel('Euclidean distance in the space with other variables')
#
#     plt.draw()
#     plt.pause(2)
#     plt.clf()


currenciesx = ['USD', 'EUR', 'GBP', 'JPY',]# 'CHF', ]  # 'CAD',]# 'AUD',]# 'NZD']

fx = ForexMarket(currenciesx)

class DynamicLeadLag:

    def __init__(self,
                 distance,
                 lead_lag,
                 ):
        self.distance = distance
        self.lead_lag = lead_lag

    def cluster_threshold(self, threshold=0.2):
        threshold = np.clip(threshold, a_min=0.05, a_max=1.05)
        distance = self.distance.copy()
        distance[distance > threshold] = 0
        return distance

    def connected_graph_clustering(self):
        x = np.linspace(0, 1, 50)
        for r in x:
            print(r)
            distance = self.distance.copy()
            distance[distance > r] = 0
            G = nx.from_numpy_matrix(distance)
            if nx.is_connected(G):
                nx.draw(G,
                        pos=nx.circular_layout(G),
                        with_labels=True,
                        node_size=1000,
                        node_color='y',
                        )  # use spring layout
                plt.draw()
                plt.show()
                return distance

    def find_lead_lag(self,threshold=0.4):
        distance = self.cluster_threshold(threshold)
        lead_lag = self.lead_lag.copy()
        for i in range(lead_lag.shape[0]):
            for j in range(lead_lag.shape[0]):
                if lead_lag[i, j] > 0:
                    if distance[i, j] > 0:

                        print(fx.symbols[i][:6] ,'leads', fx.symbols[j][:6] )

# print(ForexMarket(currenciesx).get_all_rates())
# print(ForexMarket(currenciesx).get_all_df())


while True:
    #ticks = fx.get_all_df(shift=15, time_frame=mt5.TIMEFRAME_M1)
    ticks = fx.get_all_tick_df(time_shift_min=15)

    default_config = {'normal_method': 'z_score',
                      'distance': 'euclidean'}
    distxy, ll = DynamicDistance(default_config).matrix_dynamic_distance(ticks)
    d = DynamicLeadLag(distxy, ll).find_lead_lag(0.3)
    print('=========================')
# G = nx.from_numpy_matrix(d)
# nx.draw(G,
#         pos=nx.circular_layout(G),
#         with_labels=True,
#         node_size=1000,
#         node_color='y',
#         )  # use spring layout
# plt.draw()
# plt.show()
