from datetime import datetime, timedelta
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz
import matplotlib.pyplot as plt
from scipy.stats import norm

pd.set_option('display.max_columns', 200)
pd.set_option('display.max_rows', 100)


def get_live_candle(symbol, time_shift=3000):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    timezone = pytz.timezone("Etc/GMT-3")

    time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)

    ticks = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, time_shift))
    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame.loc[last_ticks_index:, :]


def get_live_tick(symbol, time_shift=200):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    timezone = pytz.timezone("Etc/GMT-3")

    time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)

    ticks = mt5.copy_ticks_from(symbol, time_from, 100000, mt5.COPY_TICKS_ALL)

    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame.loc[last_ticks_index:, :]


def get_last_df(list_symbols):
    df = pd.DataFrame()
    for sym in list_symbols:
        x = pd.DataFrame(get_live_candle(sym).iloc[-2:-1, :])
        for c in x.columns:
            df[f'{sym[:-2]},{c}'] = x[c]
    return df


def plot_shit():
    plt.figure(11)
    a_b = get_live_candle('GBPJPY').close
    c_a = get_live_candle('EURGBP').close
    x_c_a = get_live_candle('EURJPY').close

    # a_bX =a_b + np.random.normal(0,0.045,size=len(a_b))
    # c_aX =c_a +np.random.normal(0,0.00045,size=len(c_a))
    # x_c_aX =x_c_a + np.random.normal(0,0.045,size=len(x_c_a))
    # plt.plot(abs(np.log(a_bX*c_aX/x_c_aX)))

    a_bX = a_b + np.random.normal(0, 0.005, size=len(a_b))
    c_aX = c_a + np.random.normal(0, 0.00005, size=len(c_a))
    x_c_aX = x_c_a + np.random.normal(0, 0.005, size=len(x_c_a))
    plt.plot(abs(np.log(a_bX * c_aX / x_c_aX)))

    plt.plot(abs(np.log(a_b * c_a / x_c_a)))
    plt.axhline(np.mean(abs(np.log(a_bX * c_aX / x_c_aX))), c='r')
    plt.axhline(np.mean(abs(np.log(a_b * c_a / x_c_a))), c='g')

    plt.figure(111)
    x = get_live_candle('EURGBP').close.to_numpy()
    plt.plot(x)

    x = x + np.random.normal(0, 0.00007, size=len(x))
    plt.plot(x)
    plt.show()


class Triangular:
    def __init__(self,
                 config,
                 ):
        self.config = config
        self.len_stats = 0
        self.base_states = self.gen_state()
        self.close = {}
        self.spread={}

    def gen_state(self):
        state_dict = []
        n_state = self.config['num_states']
        for i in range(-n_state, n_state + 1):
            for j in range(-n_state, n_state + 1):
                for k in range(-n_state, n_state + 1):
                    state_dict.append((i, j, k))
        self.len_stats = len(state_dict)
        states_dict = {}
        for i, state in enumerate(state_dict):
            states_dict[f'{i}'] = state
        return states_dict

    def gen_random_transition(self):
        len_states = (2 * self.config['num_states'] + 1) ** 3
        # len_states = 2**3
        matrix = np.random.rand(len_states, len_states)
        m = matrix / matrix.sum(axis=1, keepdims=1)

        # re normalize
        m[m < 1 / len_states] = 0
        # print(sum(m.flatten()))
        if not np.isnan(sum(m.flatten())):
            m = m / m.sum(axis=1, keepdims=1)

        # m2 = np.copy(m)
        #
        # m2[m2 < 2 / len_states] = 0.01
        # for i in range(m2.shape[1]):
        #     #print(m[:,1])
        #     print(sum(m2[1,:]))
        #     if sum(m2[1,:]) ==0:
        #         breakpoint()
        #
        # print(sum(m.flatten()))
        # m[0 < m < 2 / len_states] = 0.001
        #
        # if not np.isnan(sum(m.flatten())):
        #
        #     m = m / m.sum(axis=1,keepdims=1)

        return np.nan_to_num(m)

    @staticmethod
    def get_currencies( df_initial):
        xsymbols = [c[:6] for c in df_initial.columns]
        symbols = []
        for sym in xsymbols:
            if sym not in symbols:
                symbols.append(sym)

        curs = []
        for sym in symbols:
            if sym[:3] not in curs:
                curs.append(sym[:3])
            if sym[3:6] not in curs:
                curs.append(sym[3:6])

        triple_dict = {}
        for i in range(3):
            j = 0
            if i < 2:
                j = i + 1
            if f'{curs[i]}{curs[j]}' in symbols:
                triple_dict[f'{curs[i]}{curs[j]}'] = 1
            elif f'{curs[j]}{curs[i]}' in symbols:
                triple_dict[f'{curs[j]}{curs[i]}'] = -1

        return triple_dict

    @staticmethod
    def calculate_arbitrage( r_close, triple):
        arb = 1
        for sym, value in triple.items():
            if value == 1:
                arb *= r_close[sym]
            elif value == -1:
                arb /= r_close[sym]
            else:
                print('wrong value for sign of triple')
        return np.log(arb)

    def _gen_random_close(self, df_initial):
        triple = self.get_currencies(df_initial)
        symbols = triple.keys()
        st_dev = {f'{sym}': (df_initial[f'{sym},high'][0] - df_initial[f'{sym},low'][0]) / 6 for sym in symbols}
        random_close = {}
        self.close = {f'{sym}': df_initial[f'{sym},close'][0] for sym in symbols}

        r_close = {f'{sym}': df_initial[f'{sym},close'][0] + np.random.normal(scale=st_dev[sym]) for sym in symbols}
        for sym, close in r_close.items():
            random_close[f'{sym}'] = np.clip(close,
                                             a_min=df_initial[f'{sym},low'][0],
                                             a_max=df_initial[f'{sym},high'][0])
        return random_close

    def _calculate_diff_point(self, random_close, df_initial):
        triple = self.get_currencies(df_initial)
        symbols = triple.keys()
        diff = {}
        for sym in symbols:
            diff[f'{sym}'] = (random_close[sym] - df_initial[f'{sym},open'][0])
            symx = f'{sym}_i'
            point = mt5.symbol_info(symx)._asdict()['point']
            diff[f'{sym}'] /= point
        return diff

    @staticmethod
    def _calculate_prob(index_states):

        count_st = {i: index_states.count(i) for i in index_states}
        prob = np.zeros(tr.len_stats)
        for i, k in count_st.items():
            prob[int(i)] = k
        prob /= len(index_states)
        return prob

    def gen_initial_state(self, df_initial):
        triple = self.get_currencies(df_initial)
        symbols = triple.keys()
        index_st = []

        for _ in range(200):
            r_close = self._gen_random_close(df_initial)
            arbitrage = self.calculate_arbitrage(r_close, triple)
            if abs(arbitrage) <= 1e-4:
                diff = self._calculate_diff_point(r_close, df_initial)
                spreads = {f'{sym}': df_initial[f'{sym},spread'][0] for sym in symbols}
                self.spread = spreads
                diff_spreads = {f'{sym}': int(diff[sym] / spreads[sym]) for sym in symbols}
                index_st.append(self.state_index(diff_spreads))
        prob_state = self._calculate_prob(index_st)

        return prob_state

    def candle_to_state(self, symbol_list, index=1):
        a_b = get_live_candle(symbol_list[0])
        c_a = get_live_candle(symbol_list[1])
        x_b_c = get_live_candle(symbol_list[2])

        a_b_tr = (a_b.high[-index] - a_b.low[-index]) / 6
        c_a_tr = (c_a.high[-index] - c_a.low[-index]) / 6
        x_b_c_tr = (x_b_c.high[-index] - x_b_c.low[-index]) / 6

        a_b.close[-index] += np.random.normal(0, a_b_tr)
        c_a.close[-index] += np.random.normal(0, c_a_tr)
        x_b_c.close[-index] += np.random.normal(0, x_b_c_tr)

        # for _ in range(100):
        #     print((a_b.close[-index]+np.random.normal(0,a_b_tr)) * (c_a.close[-index]+np.random.normal(0,c_a_tr)) / (x_b_c.close[-index]+np.random.normal(0,x_b_c_tr)))
        #
        # print(a_b.open[-index] * c_a.open[-index] / x_b_c.open[-index])
        # print(a_b.high[-index] * c_a.high[-index] / x_b_c.low[-index])
        # print(a_b.low[-index] * c_a.low[-index] / x_b_c.high[-index])

        # print(a_b.close[-index] * c_a.close[-index] / x_b_c.close[-index])
        # print(a_b.open[-index] * c_a.open[-index] / x_b_c.open[-index])
        # print(a_b.high[-index] * c_a.high[-index] / x_b_c.low[-index])
        # print(a_b.low[-index] * c_a.low[-index] / x_b_c.high[-index])
        # breakpoint()

        diff_a_b = a_b.close[-index] - a_b.open[-index]
        diff_c_a = c_a.close[-index] - c_a.open[-index]
        diff_x_b_c = x_b_c.close[-index] - x_b_c.open[-index]

        diff_a_b /= mt5.symbol_info(symbol_list[0])._asdict()['point']
        diff_c_a /= mt5.symbol_info(symbol_list[1])._asdict()['point']
        diff_x_b_c /= mt5.symbol_info(symbol_list[2])._asdict()['point']

        spreads = [a_b['spread'][-index], c_a['spread'][-index], x_b_c['spread'][-index]]
        spreads = np.clip(spreads, a_min=4, a_max=1100)
        # spreads *=2
        diff = [int(diff_a_b), int(diff_c_a), int(diff_x_b_c)]
        filter_diff = np.zeros_like(diff)

        for i, dif in enumerate(diff):
            if dif >= spreads[i]:
                filter_diff[i] = int(dif / spreads[i])
            elif dif <= -spreads[i]:
                filter_diff[i] = int(dif / spreads[i])
            else:
                filter_diff[i] = 0
        triple_close = [a_b.close[-index], c_a.close[-index], x_b_c.close[-index]]

        filter_diff = np.clip(filter_diff, a_min=-self.config['num_states'], a_max=self.config['num_states'])
        return tuple(filter_diff), triple_close

    def state_index(self, diff_spreads):
        state = [val for val in diff_spreads.values()]

        state = np.clip(state, a_min=-self.config['num_states'], a_max=self.config['num_states'])
        state = tuple(state)
        return list(self.base_states.keys())[list(self.base_states.values()).index(state)]

    @staticmethod
    def state_transition(initial_state, transition_matrix):
        state_t = transition_matrix @ initial_state
        state_t[state_t < 1 / len(state_t)] = 0
        state_t /= sum(state_t)
        return state_t

    def rates_transition(self,state_transition):
        close = self.close
        print(close)
        for i, (sym , rate) in enumerate(close.items()):
            symx = f'{sym}_i'
            point = mt5.symbol_info(symx)._asdict()['point']
            close[sym] += state_transition[i]*self.spread[sym]*point
            #print(sym,rate,point,self.spread[sym],self.spread[sym]*point)
        return close

symbolsx = ['GBPJPY_i', 'EURGBP_i', 'EURJPY_i', ]
df = get_last_df(symbolsx)
tr = Triangular(config={'num_states': 1, })
in_state = tr.gen_initial_state(df)
print(tr.close)
#for _ in range(100):
transition_prob = tr.gen_random_transition()
state = tr.state_transition(in_state, transition_prob)
print(state)
print(tr.rates_transition((1,0,-1)))
close_t = tr.rates_transition((1,0,-1))
triple = tr.get_currencies(df)
print(tr.calculate_arbitrage(close_t,triple))
