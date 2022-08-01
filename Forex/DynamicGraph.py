# # TEST CLASS
from DynamicDistance import DynamicDistance
# TEST CLASS
from LiveRate import ForexMarket


# Dendrogram (Single Linkage)
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as sch
import scipy.spatial.distance as dist
import numpy as np


while True:

    currenciesx = ['USD', 'EUR', 'GBP', 'JPY', 'CHF',]# 'CAD',]# 'AUD',]# 'NZD']
    #print(ForexMarket(currenciesx).get_all_rates())
    #print(ForexMarket(currenciesx).get_all_df())
    fx = ForexMarket(currenciesx)
    #ticks = fx.get_all_df(shift=30)
    ticks = fx.get_all_tick_df(time_shift_min=30)

    #print(ticks)
    default_config = {'normal_method': 'z_score',
                      'distance': 'euclidean'}
    distxy = DynamicDistance(default_config).matrix_dynamic_distance(ticks)
    plt.figure(1211)

    link_distance = dist.squareform(distxy)
    link_distance -= np.min(link_distance)
    link_distance /= (np.max(link_distance) - np.min(link_distance))
    link_distance += 0.05
    Z = sch.linkage(link_distance, method='single')
    den = sch.dendrogram(Z,labels=fx.symbols)
    plt.title('Dendrogram (Single Linkage) for the clustering of the dataset')
    plt.xlabel('Data Points Number')
    plt.ylabel('Euclidean distance in the space with other variables')



    plt.draw()
    plt.pause(15)
    plt.clf()
