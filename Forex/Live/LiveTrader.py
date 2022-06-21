from Forex.Market import LiveTicks
from Forex.ManageOrder import ManageOrder

import time


class LiveTrader:
    def __init__(self,
                 config,
                 ):
        self.manager = ManageOrder(config['symbol'])
        self.live = LiveTicks(config)
        self.agent = config['agent']
        self.last_tick = self.live.get_rates().index[-1]
    def _check_new_tick(self):
        tick = self.live.get_rates().index[-1]
        if tick > self.last_tick:
            self.last_tick = tick
            return True
        else:
            return False

    def main(self):
        while True:
            if self._check_new_tick():
                df = self.live.get_rates()

                request = self.agent.take_action(df)
                if request != {}:
                    self.manager.manage(request)
                else:
                    pass
            else:
                print(self.last_tick)

                pass
            time.sleep(5)


from Trader.Strategy.ScaplerStrategy import Scalper
from Forex.Agent import Agent
live_config = {'symbol': 'XAUUSD',
               'window':600,
               'agent': Agent(Scalper)}
live_trader = LiveTrader(config=live_config)
live_trader.main()