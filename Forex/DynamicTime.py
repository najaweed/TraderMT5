import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz
# Plotting Packages
import matplotlib.pyplot as plt
import seaborn as sbn

import matplotlib as mpl


# mpl.rcParams['figure.dpi'] = 300
# savefig_options = dict(format="png", dpi=300, bbox_inches="tight")

def get_live_candle(symbol, time_shift=12 * 5, start=0):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    timezone = pytz.timezone("Etc/GMT-3")

    time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)

    ticks = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, start, time_shift))
    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame.loc[last_ticks_index:, :]


# Computation packages
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw


def compute_euclidean_distance_matrix(x, y) -> np.array:
    """Calculate distance matrix
    This method calcualtes the pairwise Euclidean distance between two sequences.
    The sequences can have different lengths.
    """
    dist = np.zeros((len(y), len(x)))
    for i in range(len(y)):
        for j in range(len(x)):
            dist[i, j] = (x[j] - y[i]) ** 2
    return dist


def compute_accumulated_cost_matrix(x, y) -> np.array:
    """Compute accumulated cost matrix for warp path using Euclidean distance
    """
    distances = compute_euclidean_distance_matrix(x, y)

    # Initialization
    cost = np.zeros((len(y), len(x)))
    cost[0, 0] = distances[0, 0]

    for i in range(1, len(y)):
        cost[i, 0] = distances[i, 0] + cost[i - 1, 0]

    for j in range(1, len(x)):
        cost[0, j] = distances[0, j] + cost[0, j - 1]

        # Accumulated warp path cost
    for i in range(1, len(y)):
        for j in range(1, len(x)):
            cost[i, j] = min(
                cost[i - 1, j],  # insertion
                cost[i, j - 1],  # deletion
                cost[i - 1, j - 1]  # match
            ) + distances[i, j]

    return cost


time1 = np.linspace(start=0, stop=1, num=150)
time2 = time1

# x1 = 4 * np.sin(3*np.pi * time1) #+ 1.5 * np.sin(4*np.pi * time1)
# x2 = 3 * np.sin(3*np.pi * time2 + 0.5) #+ 1.5 * np.sin(4*np.pi * time2 + 0.5)
import numpy as np




def _dtw_pair(symbol):
    df1 = get_live_candle(symbol[0]).close.to_numpy()
    df2 = get_live_candle(symbol[1]).close.to_numpy()

    df1 -= df1.min()
    df1 /= (df1.max() - df1.min())

    df2 -= df2.min()
    df2 /= (df2.max() - df2.min())

    # df3 = get_live_tick('EURGBP_i').close.to_numpy()
    # warp_path, distance, mapping_1, mapping_2 = xdtw(df1, df2)
    # print(cost)
    distance, warp_path = fastdtw(df1, df2, radius=len(df1), dist=euclidean)
    # print(distance)
    return distance
    # fig, ax = plt.subplots(figsize=(16, 12))
    #
    # # Remove the border and axes ticks
    # fig.patch.set_visible(False)
    # ax.axis('off')
    # print(distance)
    # for [map_x, map_y] in warp_path:
    #     ax.plot([map_x, map_y], [df1[map_x], df2[map_y]], '-k')
    #
    # ax.plot(df1, color='blue', marker='o', markersize=10, linewidth=5)
    # ax.plot(df2, color='red', marker='o', markersize=10, linewidth=5)
    # ax.tick_params(axis="both", which="major", labelsize=18)
    # fig.show()


def get_symbols(currencies):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

    all_sym = mt5.symbols_get()
    market_symbols = [sym.name for sym in all_sym]

    symbols = []
    for i_1, c_1 in enumerate(currencies):
        for i_2, c_2 in enumerate(currencies):
            if c_1 != c_2:
                if f'{c_1}{c_2}_i' in market_symbols:
                    # print(f'{c_1}{c_2}')
                    symbols.append({'symbol': f'{c_1}{c_2}_i',
                                    'source': c_1,
                                    'target': c_2,
                                    's_t': (c_1, c_2),
                                    'i_j': (i_1, i_2)
                                    })
    return symbols


def distance_matrix(symbols):
    dist = np.zeros((len(symbols), len(symbols)))
    for i, i_sym in enumerate(symbols):
        for j, j_sym in enumerate(symbols):
            dist[i, j] = _dtw_pair((i_sym, j_sym))
            dist[j, i] = dist[i, j]

    max = np.max(dist)
    dist[dist == 0] = np.inf
    min = np.min(dist)
    dist -= min
    dist /= (max - min)
    dist[dist == np.inf] = 0
    return dist


currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', ]#'AUD', 'NZD']

symbols_info = get_symbols(currencies)

symbol_list = [sym['symbol'] for sym in symbols_info]
print(symbol_list)
distance = distance_matrix(symbol_list)
distance[distance > 0.1] = 0
print(distance)

adj = distance.copy()
# plt.imshow(distance)
# plt.show()
import networkx as nx

sym_dict = {i: f'{sym[:3]} {sym[3:6]}' for i, sym in enumerate(symbol_list)}
G = nx.from_numpy_matrix(adj)
G = nx.DiGraph(G)
nx.draw(G,
        #pos=nx.circular_layout(G),
        with_labels=True,
        node_size=1000,
        node_color='y',
        labels=sym_dict,
        arrows=False)

# Now only add labels to the nodes you require (the hubs in my case)
# nx.draw_networkx_labels(G,pos=nx.circular_layout(G),labels=sym_dict,font_size=16,font_color='r')

# nx.draw(G,
#         pos=nx.circular_layout(G),
#         with_labels=True,
#         node_size=1000,
#         node_color='y',
#
#         )  # use spring layout
plt.draw()
plt.show()
