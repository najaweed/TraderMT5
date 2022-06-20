import time
import MetaTrader5 as mt5
import matplotlib.pyplot as plt

from Forex.Market import LiveTicks
import numpy as np
import pandas as pd


def plt_candlestick(df: pd.DataFrame):
    open = df.open
    close = df.close
    high = df.high
    low = df.low
    time_index = df.index

    color = ["green" if close_price > open_price else "red" for close_price, open_price in
             zip(df.close.to_numpy(), df.open.to_numpy())]
    plt.bar(x=time_index,
            height=np.abs(open - close),
            bottom=np.min((open, close), axis=0),
            width=5e-4,
            color=color,
            # alpha=1/time_frame_min,
            )
    plt.bar(x=time_index,
            height=high - low,
            bottom=low,
            width=1e-4,
            color=color,
            # alpha=1/time_frame_min,
            )


from sklearn.cluster import KMeans


class LiveMicroChannel:
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()

    def __init__(self,
                 config,
                 ):
        self.live = LiveTicks(config)
        self.last_tick = self.live.get_rates().index[-1]
        self.last_channel_states = {}
        self.break_state = {}

    def _check_new_tick(self):
        tick = self.live.get_rates().index[-1]
        if tick > self.last_tick:
            self.last_tick = tick
            return True
        else:
            return False

    def _micro_channel(self, df):
        for win in reversed(range(3, 10)):
            # print(win)
            low = df.low[-win:]
            high = df.high[-win:]
            up_trend = np.all(np.diff(low.to_numpy()) >= 0) and np.all(high[0] - high.to_numpy() <= 0)
            down_trend = np.all(np.diff(high.to_numpy()) <= 0) and np.all(low[0] - low.to_numpy() >= 0)
            if up_trend:
                max_return = max(high) - low[0]
                linear_return = low[-1] - low[0]
                return 'up', win, linear_return, low[-1]  # (linear_return, max_return)
            elif down_trend:
                max_return = max(low) - high[0]
                linear_return = high[-1] - high[0]
                return 'down', win, linear_return, high[-1]  # (linear_return, max_return)

        return 'no', 0, 0, 0

    def _micro_channel_state(self, df):
        state_log = {}
        for i in reversed(range(1, 6 * 360)):
            x_df = self._gen_tick_bar(df, i)
            if x_df is not None:
                # check mirco channel situation ,
                trend, len_trend, lin_return, break_price = self._micro_channel(x_df)
                # print(i , len_trend)
                duration_trend = i * len_trend

                speed_trend = lin_return / duration_trend if duration_trend > 0 else 0
                state_log[f'{i}min'] = {'trend': trend,
                                        'speed': speed_trend,
                                        'duration': duration_trend,
                                        'break_price': break_price,
                                        }
        return state_log

    @staticmethod
    def _gen_tick_bar(df_rates, i_time_frame: int):
        df = None
        if df_rates.shape[0] > i_time_frame * 3:
            df_rates = df_rates.iloc[:-i_time_frame, :]
            df = df_rates.open.resample(f'{i_time_frame}min').first().to_frame()
            df['high'] = df_rates.high.resample(f'{i_time_frame}min').max()
            df['low'] = df_rates.low.resample(f'{i_time_frame}min').min()
            df['close'] = df_rates.close.resample(f'{i_time_frame}min').last()
        return df

    def _state_reporter(self):
        if self.last_channel_states != {}:
            for time_frame, state in self.last_channel_states.items():
                if state['trend'] != 'no':
                    print(time_frame, state)
                    color = 'red' if state['trend'] == 'down' else 'blue'
                    # plt.axhline(state['break_price'], color=color)
        # plt.show()

    def _find_num_trends(self):
        change_trend = 1
        if self.last_channel_states != {}:
            trends = []
            for time_frame, state in self.last_channel_states.items():
                if state['trend'] != 'no':
                    trends.append(state['trend'])

            for i in range(len(trends) - 1):
                if trends[i] != trends[i + 1]:
                    change_trend += 1
                else:
                    pass
        print(change_trend)

    def _spike_detection(self):
        pass

    def main(self):
        while True:

            if self._check_new_tick():
                print(self.last_tick)
                df = self.live.get_rates()
                plt_candlestick(df.iloc[-100:, :])
                self.last_channel_states = self._micro_channel_state(df)
                self._state_reporter()
                self._find_num_trends()
                # report

            #
            else:
                pass
            time.sleep(5)


config_micro_channel = {
    "symbol": 'XAUUSD',
    "window": 6666,
    # "min_tick_channel": 3,
    # "digit": 1e2,
    # "plotter": Plotter([]),
}
#
# live = LiveTicks(trader_config).get_rates()
# print(live)
# import matplotlib.pyplot as plt
# plt.plot(live.close)
# plt.show()
live_plot = LiveMicroChannel(config_micro_channel)
live_plot.main()
