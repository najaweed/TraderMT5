import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

while True:

    symb_info = mt5.symbol_info_tick('EURUSD')._asdict()
    time_from = pd.to_datetime(symb_info['time_msc'], unit='ms') - timedelta(minutes = 2)

    aud_usd = pd.DataFrame(mt5.copy_ticks_from("AUDUSD", time_from, -1, mt5.COPY_TICKS_ALL))
    nzd_usd = pd.DataFrame(mt5.copy_ticks_from("NZDUSD", time_from, -1, mt5.COPY_TICKS_ALL))
    aud_nzd = pd.DataFrame(mt5.copy_ticks_from("AUDNZD", time_from, -1, mt5.COPY_TICKS_ALL))

    #ticks_frame['time']=pd.to_datetime(ticks_frame['time_msc'], unit='ms')
    #print(aud_usd.ask.to_numpy()[-1])
    #print(nzd_usd.ask.to_numpy()[-1])
    #print(aud_nzd.ask.to_numpy()[-1])
    ask_aud_usd = aud_usd.bid.to_numpy()[-1]
    ask_nzd_usd = nzd_usd.bid.to_numpy()[-1]
    ask_aud_nzd = aud_nzd.bid.to_numpy()[-1]
    #print(np.log(ask_nzd_usd) +np.log(ask_aud_nzd) - np.log(ask_aud_usd) )
    print(ask_nzd_usd*ask_aud_nzd/ask_aud_usd )