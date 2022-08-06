from datetime import datetime, timedelta
import time
import pytz
import pandas as pd
import numpy as np
import MetaTrader5 as mt5

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()


class HistoricalCandle:
    def __init__(self,
                 symbol,
                 ):
        self.symbol = symbol

    def get_all_dfs(self):
        return {'daily': self.get_last_day(),
                'weekly': self.get_last_week(),
                'monthly': self.get_last_month(),
                'sessional': self.get_last_quarter(),
                'yearly': self.get_last_year()}

    def get_last_day(self, shift_5m=12 * 24):
        ticks = pd.DataFrame(mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 0, shift_5m))
        ticks['time'] = pd.to_datetime(ticks['time'], unit='s')
        ticks = ticks.set_index('time')
        return ticks

    def get_last_week(self, shift_15m=120 * 4):
        ticks = pd.DataFrame(mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, shift_15m))
        ticks['time'] = pd.to_datetime(ticks['time'], unit='s')
        ticks = ticks.set_index('time')
        return ticks

    def get_last_month(self, shift_1h=120 * 4):
        ticks = pd.DataFrame(mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, shift_1h))
        ticks['time'] = pd.to_datetime(ticks['time'], unit='s')
        ticks = ticks.set_index('time')
        return ticks

    def get_last_quarter(self, shift_8h=300):
        ticks = pd.DataFrame(mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H8, 0, shift_8h))
        ticks['time'] = pd.to_datetime(ticks['time'], unit='s')
        ticks = ticks.set_index('time')
        return ticks

    def get_last_year(self, shift_days=300):
        ticks = pd.DataFrame(mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_D1, 0, shift_days))
        ticks['time'] = pd.to_datetime(ticks['time'], unit='s')
        ticks = ticks.set_index('time')
        return ticks


# #TEST CLASS
# candle = HistoricalCandle('EURUSD_i')
# print(candle.get_last_year())
# print(candle.get_last_quarter())
# print(candle.get_last_month())
# print(candle.get_last_week())
# print(candle.get_last_day())


class LiveMarket:
    def __init__(self,
                 symbol):
        self.symbol = symbol

    def get_live_rates(self, shift=60 * 6, time_frame=mt5.TIMEFRAME_M1):
        ticks = pd.DataFrame(mt5.copy_rates_from_pos(self.symbol, time_frame, 0, shift))
        ticks['time'] = pd.to_datetime(ticks['time'], unit='s')
        ticks = ticks.set_index('time')
        return ticks

    def get_live_ticks(self, time_shift_min=100):
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            quit()
        timezone = pytz.timezone("Etc/GMT-3")

        time_from = datetime.now(tz=timezone) - timedelta(seconds=time_shift_min)
        ticks = mt5.copy_ticks_from(self.symbol, time_from, 100000, mt5.COPY_TICKS_ALL)
        if ticks is None:
            print('TICK ARE NOT AVAILABLE , WAIT FOR 1 sec and retry')
            time.sleep(1)
            self.get_live_ticks()

        ticks_frame = pd.DataFrame(ticks)
        ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
        ticks_frame = ticks_frame.set_index('time')
        last_ticks_index = ticks_frame.index[-1] - timedelta(seconds=time_shift_min)

        return ticks_frame.loc[last_ticks_index:, :]


# TEST CLASS
# print(LiveMarket('EURUSD_i').get_live_rates())
# print(LiveMarket('EURUSD_i').get_live_ticks())


class ForexMarket:
    def __init__(self,
                 currencies):
        self.currencies = currencies
        self.symbols = self._get_symbols()
        # self.fx_index = self.get_index_currencies()

    def _get_symbols(self):
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            quit()

        all_sym = mt5.symbols_get()
        market_symbols = [sym.name for sym in all_sym]

        symbols = []
        symbols_info = []

        for i_1, c_1 in enumerate(self.currencies):
            for i_2, c_2 in enumerate(self.currencies):
                if c_1 != c_2:
                    if f'{c_1}{c_2}_i' in market_symbols:
                        # print(f'{c_1}{c_2}')
                        symbols_info.append({'symbol': f'{c_1}{c_2}_i',
                                             'source': c_1,
                                             'target': c_2,
                                             's_t': (c_1, c_2),
                                             'i_j': (i_1, i_2)
                                             })
                        symbols.append(f'{c_1}{c_2}_i')

        return symbols  # ,symbols_info

    def get_all_rates(self, time_shift=60, time_frame=mt5.TIMEFRAME_M15):
        all_rates = {}
        for sym in self.symbols:
            all_rates[f'{sym}'] = LiveMarket(sym).get_live_rates(time_shift, time_frame)
        return all_rates

    def get_all_df(self, shift=60 * 6, time_frame=mt5.TIMEFRAME_M1):
        all_rates = {}
        for sym in self.symbols:
            all_rates[f'{sym}'] = LiveMarket(sym).get_live_rates(shift, time_frame)
        return all_rates

    def get_all_tick_df(self, time_shift_min=3, ):
        all_rates = {}
        for sym in self.symbols:
            all_rates[f'{sym}'] = LiveMarket(sym).get_live_ticks(time_shift_min, )
        return all_rates

    def get_index_currencies(self):
        fx_index = {}
        for cur in self.currencies:
            fx_index[f'{cur}'] = []
            for sym in self.symbols:
                if cur == sym[:3]:
                    fx_index[f'{cur}'].append((1, sym))
                elif cur == sym[3:6]:
                    fx_index[f'{cur}'].append((-1, sym))
        return fx_index

    def gen_fx_indexes(self, time_shift=60, time_frame=mt5.TIMEFRAME_M15):
        fx_indexes = self.get_index_currencies()
        rates = self.get_all_rates(time_shift, time_frame)
        fx = {}
        lenx = len(next(iter(rates.values())))
        j_scale = 1
        for cur, list_sym in fx_indexes.items():
            xx = next(iter(rates.values()))
            # print(cur , list_sym )
            # fx[f'{cur}'] = \
            x_df = pd.DataFrame(columns=['open', 'high', 'low', 'close'], index=xx.index).fillna(0)
            # {'open':np.zeros(lenx),'high':np.zeros(lenx),'low':np.zeros(lenx),'close':np.zeros(lenx),}
            for sym in list_sym:
                if sym[1][3:6] == 'JPY':
                    j_scale = 1
                if sym[0] == 1:
                    x_df['open'] += np.log(rates[sym[1]]['open'] / j_scale)
                    x_df['close'] += np.log(rates[sym[1]]['close'] / j_scale)
                    x_df['high'] += np.log(rates[sym[1]]['high'] / j_scale)
                    x_df['low'] += np.log(rates[sym[1]]['low'] / j_scale)

                if sym[0] == -1:
                    x_df['open'] -= np.log(rates[sym[1]]['open'] / j_scale)
                    x_df['close'] -= np.log(rates[sym[1]]['close'] / j_scale)
                    x_df['high'] -= np.log(rates[sym[1]]['low'] / j_scale)
                    x_df['low'] -= np.log(rates[sym[1]]['high'] / j_scale)
            fx[f'{cur}'] = x_df
        return fx


# TEST CLASS
while True:

    currenciesx = ['USD', 'EUR', 'GBP', 'JPY',  'CHF',] # 'CAD', 'AUD', 'NZD']
    # print(ForexMarket(currenciesx).get_all_rates())
    # print(ForexMarket(currenciesx).get_all_df())
    x = ForexMarket(currenciesx).gen_fx_indexes(time_shift=220, time_frame=mt5.TIMEFRAME_D1)

    for cur, df in x.items():
        print(cur)
        df.rename(columns={'open': 'Open', 'high': 'High','low': 'Low','close': 'Close',}, inplace=True)
        df.index.rename('Date',inplace=True)
        #print(df.index[0])

        df.index = pd.to_datetime(df.index, format='%m/%d/%Y').strftime('%Y%m%d%H%M')
        #print(df.index[0])
        df.to_csv(f'C:\\Users\\z\\Desktop\\candle\\{cur}.csv')
    print('===')
    time.sleep(10)
# import matplotlib.pyplot as plt
# from matplotlib.pyplot import figure
# import mplfinance as mpf
# import finplot as fplt
#
# # fig, axs = plt.subplots(len(currenciesx), figsize=(10,7))
# fig = mpf.figure(figsize=(12, 12))
#
# ax1 = fig.add_subplot(2, 2, 1, style='yahoo')
# ax2 = fig.add_subplot(2, 2, 2, style='yahoo')
# ax3 = fig.add_subplot(2, 2, 3, style='yahoo')
# ax4 = fig.add_subplot(2, 2, 4, style='yahoo')
# axs = [ax1, ax2, ax3, ax4]
#
# for i, cur in enumerate(currenciesx):
#     # axs[i].plot(x[cur] , label = cur)
#     # axs[i].legend(loc='upper left')
#     # mpf.figure(cur)
#
#     # mpf.plot(pd.DataFrame(x[cur]), type='candle',style='yahoo' )
#     x = ForexMarket(currenciesx).gen_fx_indexes(time_shift=80, time_frame=mt5.TIMEFRAME_MN1)
#     if cur == 'USD':
#         mpf.plot(x[cur], ax=axs[i], axtitle=cur, type='candle', block=False)
#     else:
#         mpf.plot(x[cur], ax=axs[i], axtitle=cur, type='candle', block=False)
#
# # plt.plot(x['EUR']-x['JPY'] , label = 'EUR JPY')
#
# mpf.show()
