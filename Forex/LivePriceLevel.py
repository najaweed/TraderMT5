import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd



# all_sup_res = {}
# for time_type, ticks in xticks.items():
#     price_lvl = PriceLevel(ticks).point_for_plot()
#
#     all_sup_res[f'{time_type}'] = price_lvl
# print(all_sup_res)

#
# seq_of_points = prepare_for_plot(price_lvl)
# print(seq_of_points)
# xticks = hc.get_last_quarter()
# mpf.plot(ticks, type='candle', alines=seq_of_points)

class PlotPriceLevel:
    def __init__(self,
                 all_df_list: dict,
                 plot_df: pd.DataFrame):
        self.df = plot_df
        self.all_df_list = all_df_list

        self.sup_res = self._get_all_price_level()
        self.lines_config = self._prepare_dict_aline_mpl()
        self.ylim = (self.df.low.min()*0.999,self.df.high.max()*1.001,)
    def _clip_datetime(self, line):
        start_datetime = self.df.index[0]
        end_datetime = self.df.index[-1]

        if line[0][0] < start_datetime:
            line[0] = (start_datetime, line[0][1])

        # if line[1][0] > end_datetime:
        line[1] = (end_datetime, line[1][1])
        return line

    def _get_all_price_level(self):
        all_sup_res = {}
        for time_type, ticks in self.all_df_list.items():
            price_lvl = PriceLevel(ticks).point_for_plot()
            all_sup_res[f'{time_type}'] = price_lvl
        return all_sup_res

    def _prepare_dict_aline_mpl(self, ):
        all_lines = []
        color = []
        linewidths = []
        for time_frame, sup_res in self.sup_res.items():
            for line_type, line in sup_res.items():
                line = self._clip_datetime(line)
                all_lines.append(line)
                if line_type == 'support':
                    color.append('blue')
                elif line_type == 'resistance':
                    color.append('red')

                if time_frame == 'yearly':
                    linewidths.append(60)
                elif time_frame == 'sessional':
                    linewidths.append(30)
                elif time_frame == 'monthly':
                    linewidths.append(21)
                elif time_frame == 'weekly':
                    linewidths.append(14)
                elif time_frame == 'daily':
                    linewidths.append(5)

        line_config = dict(alines=all_lines,
                           alpha=0.2,
                           colors=color,
                           linewidths=linewidths)

        return line_config

    def mpl_plot(self):

        mpf.plot(self.df, type='candle',ylim=self.ylim , alines= self.lines_config )
        plt.show()



from LiveRate import HistoricalCandle
from PriceLevel import PriceLevel

hc = HistoricalCandle('CHFJPY_i')
ppl = PlotPriceLevel(hc.get_all_dfs(), hc.get_last_day(12*12))
ppl.mpl_plot()
