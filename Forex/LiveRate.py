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
        return {'daily':self.get_last_day(),
                'weekly':self.get_last_week(),
                'monthly':self.get_last_month(),
                'sessional':self.get_last_quarter(),
                'yearly':self.get_last_year()}

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

        time_from = datetime.now(tz=timezone) - timedelta( minutes=time_shift_min)
        ticks = mt5.copy_ticks_from(self.symbol, time_from, 100000, mt5.COPY_TICKS_ALL)

        ticks_frame = pd.DataFrame(ticks)
        ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
        ticks_frame = ticks_frame.set_index('time')
        return ticks_frame

# TEST CLASS
# print(LiveMarket('EURUSD_i').get_live_rates())
# print(LiveMarket('EURUSD_i').get_live_ticks())




class ForexMarket:
    def __init__(self,
                 currencies):
        self.currencies = currencies
        self.symbols = self._get_symbols()

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

    def get_all_rates(self):
        all_rates = {}
        for sym in self.symbols:
            all_rates[f'{sym}'] = LiveMarket(sym).get_live_rates().to_numpy()
        return all_rates

    def get_all_df(self,shift=60 * 6, time_frame=mt5.TIMEFRAME_M1):
        all_rates = {}
        for sym in self.symbols:
            all_rates[f'{sym}'] = LiveMarket(sym).get_live_rates(shift,time_frame)
        return all_rates

    def get_all_tick_df(self,time_shift_min=3,):
        all_rates = {}
        for sym in self.symbols:
            all_rates[f'{sym}'] = LiveMarket(sym).get_live_ticks(time_shift_min,)
        return all_rates

# # TEST CLASS
# currenciesx = ['USD', 'EUR', 'GBP', ]#'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
# print(ForexMarket(currenciesx).get_all_rates())
# print(ForexMarket(currenciesx).get_all_df())
# x =ForexMarket(currenciesx).get_all_df()
# print(x['EURGBP_i']['high'])