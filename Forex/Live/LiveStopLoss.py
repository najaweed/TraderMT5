import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time

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

        self.saved_profit = self.config['min_profit'] * self.point
        self.last_sl_price = 0

    def get_opened_positions(self):
        positions = mt5.positions_get(symbol=self.config['symbol'])
        sym_positions = []
        for i_pos, pos in enumerate(positions):
            pos = pos._asdict()
            sym_positions.append(pos)
        return sym_positions

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
            if position['price_open'] - position['price_current'] >= self.config['min_profit'] * self.point:
                new_sl_price = position['price_current'] + self.config['trail_stop_loss'] * self.point
                if new_sl_price < self.last_sl_price:
                    print('trail sl ', self.last_sl_price, new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price

        elif position['type'] == mt5.ORDER_TYPE_BUY:
            if position['price_current'] - position['price_open'] >= self.config['min_profit'] * self.point:
                new_sl_price = position['price_current'] - self.config['trail_stop_loss'] * self.point
                if new_sl_price > self.last_sl_price:
                    print('trail sl  from', self.last_sl_price, 'to', new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price
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
          'min_profit': 60,
          'stop_loss': 100,
          'trail_stop_loss': 30,
          }
live_sl = LiveStopLoss(config)
live_sl.main()
