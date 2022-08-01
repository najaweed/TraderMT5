import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import time
import MetaTrader5 as mt5
import pytz

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

def get_symbols(currencies):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

    all_sym = mt5.symbols_get()
    market_symbols = [sym.name for sym in all_sym]

    symbols = []
    symbols_info = []

    for i_1, c_1 in enumerate(currencies):
        for i_2, c_2 in enumerate(currencies):
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

    return symbols#,symbols_info


currencies = ['USD', 'EUR', 'GBP', ]#'JPY', 'CHF', 'CAD', 'AUD', 'NZD']

symbols_info = get_symbols(currencies)


def get_live_candle(symbol, time_shift=120*3, start=0):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    timezone = pytz.timezone("Etc/GMT-3")

    time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)

    #ticks = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, start, time_shift))
    ticks = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, time_shift))

    ticks_frame = pd.DataFrame(ticks)
    ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
    ticks_frame = ticks_frame.set_index('time')
    last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
    return ticks_frame#.loc[last_ticks_index:, :]

def gen_all_symbol_rates(symbols):
    all_rates = {}
    for sym in symbols:
        all_rates[f'{sym}'] = get_live_candle(sym).close.to_numpy()

    return all_rates
#print(gen_all_symbol_rates(symbols_info))
ticks = gen_all_symbol_rates(symbols_info)
#print(ticks)
