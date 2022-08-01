import networkx as nx
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz




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
                    #print(f'{c_1}{c_2}')
                    symbols.append({'symbol': f'{c_1}{c_2}_i',
                                    'source': c_1,
                                    'target': c_2,
                                    's_t': (c_1, c_2),
                                    'i_j': (i_1, i_2)
                                    })
    return symbols




def _gen_graph():
    #
    # import itertools
    #
    # print(list(itertools.combinations(currencies, 8)))
    #
    #
    # def get_triple(symbols_info, p_currencies):
    #     symbol = [sym['symbol'] for sym in symbols_info]
    #     all_loop = []
    #     print(p_currencies, symbol)
    #     for k in range(3,len(p_currencies)+1):
    #         curs = list(itertools.combinations(p_currencies, k))
    #         for currencies in curs:
    #             triple_dict = {}
    #             for i in range(k):
    #                 j = 0
    #                 if i < k - 1:
    #                     j = i + 1
    #                 if f'{currencies[i]}{currencies[j]}' in symbol:
    #                     triple_dict[f'{currencies[i]}{currencies[j]}'] = 1
    #                 elif f'{currencies[j]}{currencies[i]}' in symbol:
    #                     triple_dict[f'{currencies[j]}{currencies[i]}'] = -1
    #
    #             all_loop.append(triple_dict)
    #
    #     return all_loop
    #
    # al = get_triple(symbols_info, currencies)
    # for loop in al:
    #     print(loop)

    G = nx.DiGraph()

    for sym in symbols_info:
        pass

    G.add_weighted_edges_from([(0, 1, 2), (1, 2, 2), (2, 0, 1), (1, 4, 2), (4, 0, -5)])
    for node in G.nodes:
        bell = nx.find_negative_cycle(G, node)
        print(bell)

    nx.draw(G,
            pos=nx.circular_layout(G),
            with_labels=True,
            node_size=1000,
            node_color='y',
            )  # use spring layout
    plt.draw()
    plt.show()


def get_live_tick(symbol, time_shift=200):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    timezone = pytz.timezone("Etc/GMT-3")
    utc_from = datetime(2022, 7, 26,hour=15, tzinfo=timezone)
    utc_to = datetime(2022, 7, 26,hour=16, tzinfo=timezone)
    # request AUDUSD ticks within 11.01.2020 - 11.01.2020
    ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_ALL)
    #print(ticks)
    #ticks = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, utc_from, utc_to)
    #print("Ticks received:", len(ticks))

    # time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)
    #
    # ticks = mt5.copy_ticks_from(symbol, time_from, 100000, mt5.COPY_TICKS_ALL)
    # print(ticks)
    # breakpoint()
    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    # last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame  # .loc[last_ticks_index:, :]

def _gen_matrix_mt5(symbols_info):
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']

    matrix = np.zeros((len(currencies),len(currencies)))
    for i, sym in enumerate(symbols_info):
        tick = get_live_tick(sym['symbol'])
        tick = tick.iloc[-1,:]
        i,j=sym['i_j']
        if i > j :
            #print(sym['i_j'],sym['s_t'])
            matrix[i][j] = 1/tick.ask#-np.log(tick.ask)
            matrix[j][i] = tick.bid#np.log(tick.bid)
        elif j > i:
            #print('aaaaa',sym['i_j'],sym['s_t'])

            matrix[i][j] = tick.bid#np.log(tick.bid)
            matrix[j][i] = 1/tick.ask#-np.log(tick.ask)

    #print(matrix)
    return matrix

currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']

symbols_info = get_symbols(currencies)

print(symbols_info)

adj = _gen_matrix_mt5(symbols_info)
print(adj)
G = nx.from_numpy_matrix(adj)
G = nx.DiGraph(G)

for node in G.nodes:
    bell = nx.find_negative_cycle(G, node)
    print(bell)

nx.draw(G,
        pos=nx.circular_layout(G),
        with_labels=True,
        node_size=1000,
        node_color='y',
        )  # use spring layout
plt.draw()
plt.show()