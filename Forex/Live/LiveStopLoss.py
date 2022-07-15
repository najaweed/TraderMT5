from datetime import datetime, timedelta
import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pytz

if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
timezone = pytz.timezone("Etc/GMT-3")


class LiveStopLoss:
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

    def __init__(self,
                 c_config,
                 ):
        self.config = c_config
        self.point = mt5.symbol_info(self.config['symbol'])._asdict()['point']
        self.last_sl_price = None
        self.sl_point = None
        self.tp_point = None

    def get_opened_positions(self):
        positions = mt5.positions_get(symbol=self.config['symbol'])
        sym_positions = []
        for i_pos, pos in enumerate(positions):
            pos = pos._asdict()
            sym_positions.append(pos)
        return sym_positions

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
        tp_price = 0
        if position['type'] == mt5.ORDER_TYPE_SELL:
            if stop_loss_price is not None:
                sl_price = stop_loss_price
            elif stop_loss_price is None:
                sl_price = position['price_current'] + self.config['stop_loss'] * self.point
                self.last_sl_price = sl_price
                print('Position Sell without SL , set automatic SL_price', sl_price)

            if position['tp'] == 0:
                tp_price = position['price_current'] - 3 * self.config['stop_loss'] * self.point
                print('Position Sell without TP, Set Automatic in ', tp_price)

            else:
                tp_price = position['tp']

        elif position['type'] == mt5.ORDER_TYPE_BUY:
            if stop_loss_price is not None:
                sl_price = stop_loss_price
            elif stop_loss_price is None:
                sl_price = position['price_current'] - self.config['stop_loss'] * self.point
                self.last_sl_price = sl_price
                print('Position Buy without SL, Set Automatic in ', sl_price)

            if position['tp'] == 0:
                tp_price = position['price_current'] + 3 * self.config['stop_loss'] * self.point
                print('Position Buy without TP, Set Automatic in ', tp_price)

            else:
                tp_price = position['tp']
        else:
            pass

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position['symbol'],
            "position": position['ticket'],
            "sl": sl_price,
            "tp": tp_price,
        }

        mt5.order_send(request)

    #
    def get_live_tick(self, time_shift=20):
        time_from = datetime.now(tz=timezone) - timedelta(minutes=time_shift)

        ticks = mt5.copy_ticks_from(self.config['symbol'], time_from, 100000, mt5.COPY_TICKS_ALL)
        if ticks is None:
            print('TICK ARE NOT AVAILABLE , WAIT FOR 1 sec and retry')
            time.sleep(1)
            self.get_live_tick()

        ticks_frame = pd.DataFrame(ticks)
        ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
        ticks_frame = ticks_frame.set_index('time')
        last_ticks_index = ticks_frame.index[-1] - timedelta(minutes=time_shift)
        return ticks_frame.loc[last_ticks_index:, :]

    @staticmethod
    def pull_back_buy(ticks_bid, pull_back_threshold):
        threshold = 0

        diff_bid = ticks_bid.diff().tail(20).to_numpy()
        for x in reversed(diff_bid):
            # print(threshold)
            if x > 0:
                threshold = 0
            elif x <= 0:
                threshold += x
            if threshold < -pull_back_threshold:
                print(f'Break Buy Pull Back Threshold {pull_back_threshold} by {threshold}')
                return True
        return False

    @staticmethod
    def pull_back_sell(ticks_ask, pull_back_threshold):
        threshold = 0
        diff_ask = ticks_ask.diff().tail(20).to_numpy()
        for x in reversed(diff_ask):
            if x < 0:
                threshold = 0
            elif x >= 0:
                threshold += x
            if threshold > pull_back_threshold:
                print(f'Break Sell Pull Back Threshold {(pull_back_threshold)} by {threshold}')
                return True
            # print(f'High Freq pullback {threshold} , threshold live {pull_back_threshold}')
        return False

    def _set_threshold_pull_back(self, spread, profit_point):
        min_threshold = spread / 3
        max_threshold = self.sl_point / 3
        profit_point = profit_point - self.sl_point
        if profit_point > 0:
            threshold = max_threshold * (1 - profit_point / self.tp_point)
        else:
            threshold = max_threshold
        threshold = np.clip(threshold, min_threshold, max_threshold)
        # print(f'Threshold live {int(threshold / self.point)}')
        return threshold

    #

    def trail_stop_loss(self, position):
        if position['type'] == mt5.ORDER_TYPE_SELL:
            profit_point = position['price_open'] - position['price_current']
            if profit_point >= 1 * self.sl_point:
                new_sl_price = position['price_current'] + self.sl_point
                if new_sl_price < self.last_sl_price:
                    self.set_stop_loss(position, new_sl_price)
                    print('Trail  Stop Loss  from', self.last_sl_price, 'to', new_sl_price)
                    self.last_sl_price = new_sl_price

                if self.config['high_freq_pull_back']:
                    ticks = self.get_live_tick()
                    spread = float(ticks.ask[-1] - ticks.bid[-1])

                    pull_back_threshold = self._set_threshold_pull_back(spread, profit_point)
                    if self.pull_back_sell(ticks.ask, pull_back_threshold):
                        print('Pull Back of Sell Position - Close Position')
                        self.close_opened_position(position)

        elif position['type'] == mt5.ORDER_TYPE_BUY:
            profit_point = position['price_current'] - position['price_open']
            if profit_point >= 1 * self.sl_point:
                new_sl_price = position['price_current'] - self.sl_point
                if new_sl_price > self.last_sl_price:
                    self.set_stop_loss(position, new_sl_price)
                    print('Trail  Stop Loss  from', self.last_sl_price, 'to', new_sl_price)
                    self.last_sl_price = new_sl_price

                if self.config['high_freq_pull_back']:
                    ticks = self.get_live_tick()
                    spread = float(ticks.ask[-1] - ticks.bid[-1])
                    pull_back_threshold = self._set_threshold_pull_back(spread, profit_point)
                    if self.pull_back_buy(ticks.bid, pull_back_threshold):
                        print('Pull Back of Buy Position - Close Position')
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
                        positions_x = self.get_opened_positions()[0]
                        if positions_x['ticket'] == position['ticket']:
                            self.last_sl_price = positions_x['sl']
                            self.sl_point = abs(positions_x['sl'] - positions_x['price_open'])
                            self.tp_point = 2 * self.sl_point
                            print(f'Set Automatic Trail Stop Loss  in {int(self.sl_point / self.point)} point ')
                            print(f'Set Automatic Take Profit in {int(self.tp_point / self.point)} point ')

                    elif position['sl'] != 0 and self.last_sl_price is None:
                        self.last_sl_price = position['sl']
                        self.sl_point = abs(position['sl'] - position['price_open'])
                        print(f'Set Trail Stop Loss from Position in {int(self.sl_point / self.point)} point ')

                        if position['tp'] != 0:
                            self.tp_point = abs(position['tp'] - position['price_open'])
                            print(f'Set Take Profit from Position in {int(self.tp_point / self.point)} point ')
                        elif position['tp'] == 0:
                            self.tp_point = 2 * self.sl_point
                            print(f'Set Automatic Take Profit in {int(self.tp_point / self.point)} point ')

                    else:
                        self.trail_stop_loss(position)
            else:
                print(f'No Position in {self.config["symbol"]}')
                time.sleep(1)
            time.sleep(1)


config = {
    'symbol': 'GBPJPY',
    'stop_loss': 30,
    'high_freq_pull_back': True,
}
live_sl = LiveStopLoss(config)
live_sl.main()
