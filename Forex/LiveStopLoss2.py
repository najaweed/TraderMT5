from datetime import datetime, timedelta
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

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
        self.last_sl_price = 0
        self.cooldown = True

    def get_opened_positions(self):
        positions = mt5.positions_get(symbol=self.config['symbol'])
        sym_positions = []
        for i_pos, pos in enumerate(positions):
            pos = pos._asdict()
            sym_positions.append(pos)
        return sym_positions

    def get_live_tick(self, time_shift=5):
        time_from = datetime.utcnow() - timedelta(minutes=time_shift)
        ticks = mt5.copy_ticks_from(self.config['symbol'], time_from, 100000, mt5.COPY_TICKS_ALL)
        return pd.DataFrame(ticks)

    def close_opened_position(self, position):

        deal_type = 0.
        deal_price = 0.
        last_deal_type = position['type']

        # last_deal_volume = position['volume']/2 if position['volume'] >=0.01 else 0.01
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

    def pull_back_buy(self, ticks_bid):
        threshold = 0

        diff_bid = ticks_bid.diff().tail(20).to_numpy()
        for x in reversed(diff_bid):
            # print(threshold)
            if x > 0:
                threshold = 0
            elif x <= 0:
                threshold += x
            if threshold < -float(self.config['pull_back_threshold'] * self.point):
                print(f'break threshold buy - {threshold}')
                return True
        return False

    def pull_back_sell(self, ticks_ask):
        threshold = 0
        diff_ask = ticks_ask.diff().tail(20).to_numpy()
        for x in reversed(diff_ask):
            # print(threshold)
            if x < 0:
                threshold = 0
            elif x >= 0:
                threshold += x
            if threshold > float(self.config['pull_back_threshold'] * self.point):
                print(f'break threshold sell - {threshold}')
                return True
        return False

    def trail_stop_loss(self, position):

        if position['type'] == mt5.ORDER_TYPE_SELL:
            #('position SELL ')
            position_profit = position['price_current'] - position['price_open']

            if 2 * self.config['min_profit'] * self.point > position_profit >= self.config[
                'min_profit'] * self.point:
                # simple fixed sl
                new_sl_price = position['price_current'] + self.config['trail_stop_loss'] * self.point
                if new_sl_price < self.last_sl_price:
                    print('trail 1 sl ', self.last_sl_price, new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price

                # cooldown
                if self.config["cooldown_strategy"][0]:
                    if self.cooldown:
                        self.cooldown = False
                        print(f'sleep {self.config["cooldown_strategy"][1]} second')
                        time.sleep(self.config["cooldown_strategy"][1])

            if position_profit >= 2 * self.config['min_profit'] * self.point:
                # simple fixed sl
                new_sl_price = position['price_current'] + 10 * self.point
                if new_sl_price < self.last_sl_price:
                    print('trail 2 sl ', self.last_sl_price, new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price

                # pull-back sell
                ticks = self.get_live_tick()
                if self.pull_back_sell(ticks.ask):
                    print('pull back of sell position - Close Position')
                    self.close_opened_position(position)

        elif position['type'] == mt5.ORDER_TYPE_BUY:
            # print('position BUY ')
            position_profit = position['price_current'] - position['price_open']
            if 2 * self.config['min_profit'] * self.point > position_profit >= self.config['min_profit'] * self.point:
                # simple fixed sl
                new_sl_price = position['price_current'] - self.config['trail_stop_loss'] * self.point
                if new_sl_price > self.last_sl_price:
                    print('trail 1 sl  from', self.last_sl_price, 'to', new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price

                # cooldown
                if self.config["cooldown_strategy"][0]:
                    if self.cooldown:
                        self.cooldown = False
                        print(f'sleep {self.config["cooldown_strategy"][1]} second')
                        time.sleep(self.config["cooldown_strategy"][1])

            if position_profit >= 2 * self.config['min_profit'] * self.point:
                new_sl_price = position['price_current'] - 10 * self.point
                if new_sl_price > self.last_sl_price:
                    print('trail 2 sl  from', self.last_sl_price, 'to', new_sl_price)
                    self.set_stop_loss(position, new_sl_price)
                    self.last_sl_price = new_sl_price

                ticks = self.get_live_tick()
                if self.pull_back_buy(ticks.bid):
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
                self.cooldown = True
                time.sleep(1)
            time.sleep(0.00001)


sl = 150
config = {
    'symbol': 'GBPJPY',
    'min_profit': 98,
    'stop_loss': 98,
    'trail_stop_loss': 98,
    'pull_back_threshold': 33,
    'cooldown_strategy': (False, 10)
}
live_sl = LiveStopLoss(config)
live_sl.main()
