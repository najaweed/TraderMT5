from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz

pd.set_option('display.max_columns', 200)
pd.set_option('display.max_rows', 100)


def get_live_candle(symbol, time_shift=3000, start=0):
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
        x = pd.DataFrame(get_live_candle(sym, time_shift=22000, start=2111).iloc[-2:-1, :])
        for c in x.columns:
            df[f'{sym[:-2]},{c}'] = x[c]
    return df


class InitialState:
    def __init__(self,
                 initial_df,
                 number_states: int = 1,
                 ):
        self.df = initial_df
        self.num_states = number_states
        self.len_states = (2 * number_states + 1) ** 3

        self.symbols = self._get_symbols()
        self.initial_close = {f'{sym}': self.df[f'{sym},close'][0] for sym, _ in self.symbols.items()}
        self.initial_arbitrage = self._calculate_arbitrage(self.initial_close)

        self.points = self._get_points()
        self.base_states = self._gen_base_states()
        self.spreads = {f'{sym}': self.df[f'{sym},spread'][0] for sym, _ in self.symbols.items()}
        self.point_spreads = {f'{sym}': self.spreads[sym] * self.points[sym] for sym, _ in self.symbols.items()}

    def _get_symbols(self):
        xsymbols = [c[:6] for c in self.df.columns]
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

    def _get_points(self):
        points = {}
        for sym, _ in self.symbols.items():
            p = mt5.symbol_info(f'{sym}_i')._asdict()
            p = p['point']
            points[f'{sym}'] = p
        return points

    def _gen_base_states(self):
        state_dict = []
        n_state = self.num_states
        for i in range(-n_state, n_state + 1):
            for j in range(-n_state, n_state + 1):
                for k in range(-n_state, n_state + 1):
                    state_dict.append([i, j, k])
        states_dict = {}
        for i, state in enumerate(state_dict):
            states_dict[f'{i}'] = state
        return states_dict

    def _calculate_arbitrage(self, close):
        arb = 1
        for sym, value in self.symbols.items():
            if value == 1:
                arb *= close[sym]
            elif value == -1:
                arb /= close[sym]
            else:
                print('wrong value for sign of triple')
        return np.log(arb)

    def _gen_random_close(self, ):
        random_close = {}
        for sym, _ in self.symbols.items():
            std = (self.df[f'{sym},high'][0] - self.df[f'{sym},low'][0]) / 6
            r_close = self.df[f'{sym},close'][0] + np.random.normal(scale=std)
            r_close = np.clip(r_close, a_min=self.df[f'{sym},low'][0], a_max=self.df[f'{sym},high'][0])
            random_close[f'{sym}'] = r_close
        return random_close

    def _calculate_diff_point(self, close, ):
        diff = {}
        for sym, _ in self.symbols.items():
            diff[f'{sym}'] = (close[sym] - self.df[f'{sym},open'][0])
            diff[f'{sym}'] /= self.points[sym]
            diff[f'{sym}'] /= self.spreads[sym]
            diff[f'{sym}'] = int(diff[f'{sym}'])
            diff[f'{sym}'] = int(np.clip(diff[f'{sym}'], a_min=-self.num_states, a_max=self.num_states))
        return diff

    def _state_index(self, diff_spreads):
        state = [val for val in diff_spreads.values()]
        return list(self.base_states.keys())[list(self.base_states.values()).index(state)]

    def _calculate_prob(self, index_states):
        count_st = {i: index_states.count(i) for i in index_states}
        prob = np.zeros(self.len_states)
        for i, k in count_st.items():
            prob[int(i)] = k
        prob /= len(index_states)
        return prob

    def sample_initial_state(self, number_sample=1000):
        index_st = []
        for _ in range(number_sample):
            r_close = self._gen_random_close()
            arbitrage = self._calculate_arbitrage(r_close)

            if abs(arbitrage) <= abs(self.initial_arbitrage):
                diff = self._calculate_diff_point(r_close, )
                index_st.append(self._state_index(diff))

        prob_state = self._calculate_prob(index_st)
        return prob_state

    @property
    def config_simulation(self):
        return {'symbols': self.symbols,
                'base_states': self.base_states,
                'point_spreads': self.point_spreads,
                'initial_close': self.initial_close,
                'initial_arbitrage': self.initial_arbitrage,
                'initial_state': self.sample_initial_state()}


def gen_random_transition(num_states=1):
    len_states = (2 * num_states + 1) ** 3
    matrix = np.random.rand(len_states, len_states)
    m = matrix / matrix.sum(axis=1, keepdims=1)
    m[m < 1 / len_states] = 0
    if not np.isnan(sum(m.flatten())):
        m = m / m.sum(axis=1, keepdims=1)
    return np.nan_to_num(m)


class Triple:
    def __init__(self,
                 config,
                 ):
        self.config = config
        self.point_spread = config['point_spreads']
        self.base_states = config['base_states']
        self.symbols = config['symbols']

    @staticmethod
    def state_transition(initial_state, transition_matrix):
        state_t = transition_matrix @ initial_state
        state_t[state_t < 1 / len(state_t)] = 0
        state_t /= sum(state_t)
        return state_t

    def _rates_transition(self, state_transition, close_rates):
        close = close_rates.copy()
        for i, (sym, rate) in enumerate(close_rates.items()):
            close[f'{sym}'] += state_transition[i] * self.point_spread[sym]
        return close

    def avg_price_transition(self, states, last_close_rates):
        state_price = {f'{sym}': [[], []] for sym, _ in self.symbols.items()}
        for i, state in enumerate(states):
            if state != 0:
                close_t = self._rates_transition(self.base_states[f'{i}'], last_close_rates)
                for sym, price in close_t.items():
                    state_price[f'{sym}'][0].append(price)
                    state_price[f'{sym}'][1].append(state)

        avg_close_price = {}
        for sym, _ in self.symbols.items():
            avg_close_price[f'{sym}'] = np.average(state_price[sym][0], weights=state_price[sym][1])

        return avg_close_price

    def propagate(self, input_state, last_close_price, transition_matrix):
        new_state = self.state_transition(input_state, transition_matrix)
        new_close = self.avg_price_transition(new_state, last_close_price)
        return new_state, new_close, transition_matrix

    def _calculate_arbitrage(self, close):
        arb = 1
        for sym, value in self.symbols.items():
            if value == 1:
                arb *= close[sym]
            elif value == -1:
                arb /= close[sym]
            else:
                print('wrong value for sign of triple')
        return np.log(arb)

    def check_arbitrage(self, close):
        arbitrage = self._calculate_arbitrage(close)
        if abs(arbitrage) <= abs(self.config['initial_arbitrage']):
            return True
        else:
            return False


symbols_x = ['GBPJPY_i', 'EURGBP_i', 'EURJPY_i', ]
df = get_last_df(symbols_x)
st = InitialState(df, number_states=2)
conf = st.config_simulation

tr = Triple(conf)
# print(conf['initial_close'])
print('initial_close', conf['initial_close'])


def log_close_to_df(list_log):
    symbols = list_log[0].keys()
    df = {f'{sym}': [] for sym in symbols}
    for log in list_log:
        # print(log)
        for sym in symbols:
            df[sym].append(log[sym])
    return pd.DataFrame.from_dict(df)


for _ in range(14000):

    trans_matrix = gen_random_transition(2)

    last_close = conf['initial_close']
    in_states = conf['initial_state']

    log_closes = []
    # print(last_close)

    log_closes.append(last_close)
    # print(log_closes)

    a = tr.propagate(in_states, last_close, trans_matrix, )
    if tr.check_arbitrage(a[1]):
        log_closes.append(a[1])

        for i in range(1000):
            a = tr.propagate(*a)
            if tr.check_arbitrage(a[1]):
                # print(a[1])
                log_closes.append(a[1])

                pass
            else:
                # print(i)
                break
    # print(log_closes)

    df_x = log_close_to_df(log_closes)
    # print(df_x.shape[0])
    if df_x.shape[0] > 150:
        for i, (sym, _) in enumerate(tr.symbols.items()):
            plt.figure(i + 1)
            plt.plot(df_x.loc[:, sym])

plt.show()
