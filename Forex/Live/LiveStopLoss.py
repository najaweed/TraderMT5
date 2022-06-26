import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()


class LiveStopLoss:
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

    def __init__(self,
                 c_config,
                 ):

        self.config = c_config
        self.point = mt5.symbol_info(self.config['symbol'])._asdict()['point']
        self.last_trail_tick = None

        # self.saved_profit = self.config['min_profit'] * self.point
        self.last_sl_price = 0

    def get_opened_positions(self):
        positions = mt5.positions_get(symbol=self.config['symbol'])
        sym_positions = []
        for i_pos, pos in enumerate(positions):
            pos = pos._asdict()
            sym_positions.append(pos)
        return sym_positions

    def get_live_tick(self, time_shift=3):
        time_from = datetime.utcnow() - timedelta(minutes=time_shift)
        ticks = mt5.copy_ticks_from(self.config['symbol'], time_from, 100000, mt5.COPY_TICKS_ALL)
        return pd.DataFrame(ticks)

    def close_opened_position(self, position):

        deal_type = 0.
        deal_price = 0.
        last_deal_type = position['type']

        #last_deal_volume = position['volume']/2 if position['volume'] >=0.1 else 0.1
        last_deal_volume = position['volume']

        if last_deal_type == mt5.ORDER_TYPE_BUY:
            deal_type = mt5.ORDER_TYPE_SELL
            deal_price = mt5.symbol_info_tick(self.config['symbol']).bid

        elif last_deal_type == mt5.ORDER_TYPE_SELL:
            deal_type = mt5.ORDER_TYPE_BUY
            deal_price = mt5.symbol_info_tick(self.config['symbol']).ask

        position_id = position['ticket']
        deviation = 2

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.config['symbol'],
            "volume": last_deal_volume,
            "type": deal_type,
            "position": position_id,
            "price": deal_price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_SPECIFIED,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        mt5.order_send(request)

    def set_stop_loss(self, position, stop_loss_price=None):
        sl_price = 0
        if position['type'] == mt5.ORDER_TYPE_SELL:
            if stop_loss_price is not None:
                sl_price = stop_loss_price
            else:
                sl_price = position['price_current'] + self.config['stop_loss'] * self.point
                self.last_sl_price = sl_price
                print('new SL', sl_price)

        elif position['type'] == mt5.ORDER_TYPE_BUY:
            if stop_loss_price is not None:
                sl_price = stop_loss_price
            else:
                sl_price = position['price_current'] - self.config['stop_loss'] * self.point
                self.last_sl_price = sl_price
                print('set new sl', sl_price)
        else:
            pass

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position['symbol'],
            "position": position['ticket'],
            "sl": sl_price,
            # "tp": tp_price,
        }

        mt5.order_send(request)

    def trail_stop_loss(self, position):

        if position['type'] == mt5.ORDER_TYPE_SELL:
            if position['profit'] >= self.config['min_profit'] * self.point:
                ticks = self.get_live_tick()
                new_sl_price = position['price_current'] + self.config['trail_stop_loss'] * self.point
                if new_sl_price < self.last_sl_price:
                    print('trail sl ', self.last_sl_price, new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price
                # bull-back
                pull_back= any(ticks.ask.diff()[-10] >= float(self.config['pull_back_threshold'] * self.point))
                if pull_back:
                    print('pull back of sell position - Close Position')
                    self.close_opened_position(position)

        elif position['type'] == mt5.ORDER_TYPE_BUY:
            if position['profit'] >= self.config['min_profit'] * self.point:
                ticks = self.get_live_tick()
                # simple fixed sl
                new_sl_price = position['price_current'] - self.config['trail_stop_loss'] * self.point
                if new_sl_price > self.last_sl_price:
                    print('trail sl  from', self.last_sl_price, 'to', new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price
                # bull-back
                pull_back = any(ticks.bid.diff()[-10] <= -float(self.config['pull_back_threshold'] * self.point))
                if pull_back:
                    # close order
                    print('pull back of buy position - Close Position')
                    self.close_opened_position(position)
        else:
            pass

    def main(self):
        while True:
            while len(self.get_opened_positions()) != 0:
                positions = self.get_opened_positions()
                for position in positions:
                    if position['sl'] == 0:
                        self.set_stop_loss(position)
                    else:
                        self.trail_stop_loss(position)
            else:
                print('no position')
                time.sleep(1)
            time.sleep(0.00001)


config = {
    'symbol': 'XAUUSD',
    'min_profit': 80,
    'stop_loss': 60,
    'trail_stop_loss': 20,
    'pull_back_threshold': 10,
}
live_sl = LiveStopLoss(config)
live_sl.main()
