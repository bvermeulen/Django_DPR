''' module for creating graphs
'''
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from seismicreport.utils.utils_funcs import nan_array
from seismicreport.utils.plogger import Logger, timed



matplotlib.use('Agg')

TICK_SPACING_PROD = 5  # x 1000
TICK_SPACING_CUMUL = 1000  # x 1000
TICK_DATE_FORMAT = mdates.DateFormatter('%d-%b-%y')

logger = Logger.getlogger()


class Mixin:

    @timed(logger, print_log=True)
    def create_daily_graphs(self):
        ''' Method to make plots. This method works correctly once self.prod_series and
            self.time_series have been calculated in method calc_totals. Reason to split
            it out of that function is that this method is time consuming and better to
            avoice to run it when it is not necessary.
        '''
        if self.prod_series and self.time_series:
            date_series = self.prod_series['date_series']
            terrain_series = self.prod_series['terrain_series']
            ctm_tuple_series = self.prod_series['ctm_series']
            assert len(date_series) == len(terrain_series), \
                'length date en terrain series must be equal'

        else:
            return

        # stacked bar plot of daily production
        t1_series = np.array([val[0] for val in terrain_series]) * 0.001
        t2_series = np.array([val[1] for val in terrain_series]) * 0.001
        t3_series = np.array([val[2] for val in terrain_series]) * 0.001
        t4_series = np.array([val[3] for val in terrain_series]) * 0.001
        t5_series = np.array([val[4] for val in terrain_series]) * 0.001
        base = np.zeros(len(date_series))

        width = 1
        plot_filename = self.media_dir / 'images/daily_prod.png'

        if any(t1_series):
            plt.bar(date_series, t1_series, width, label="Flat")
            base += t1_series

        if any(t2_series):
            plt.bar(date_series, t2_series, width, bottom=base, label="Rough")
            base += t2_series

        if any(t3_series):
            plt.bar(date_series, t3_series, width, bottom=base, label="Facilities")
            base += t3_series

        if any(t4_series):
            plt.bar(date_series, t4_series, width, bottom=base, label="Dunes")
            base += t4_series

        if any(t5_series):
            plt.bar(date_series, t5_series, width, bottom=base, label="Sabkha")

        #TODO total_sp_series = (base + t5_series) * 1000

        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_PROD))
        plt.gca().yaxis.grid()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot of cumulative production
        t1_cum = np.cumsum(t1_series)
        t2_cum = np.cumsum(t2_series)
        t3_cum = np.cumsum(t3_series)
        t4_cum = np.cumsum(t4_series)
        t5_cum = np.cumsum(t5_series)
        base = np.zeros(len(date_series))

        plot_filename = self.media_dir / 'images/cumul_prod.png'

        if any(t1_cum):
            base += t1_cum
            plt.plot(date_series, base, label="Flat")

        if any(t2_cum):
            base += t2_cum
            plt.plot(date_series, base, label="Rough")

        if any(t3_cum):
            base += t3_cum
            plt.plot(date_series, base, label="Facilities")

        if any(t4_cum):
            base += t4_cum
            plt.plot(date_series, base, label="Dunes")

        if any(t5_cum):
            base += t5_cum
            plt.plot(date_series, base, label="Sabkha")

        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_CUMUL))
        plt.gca().yaxis.grid()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot recording hours
        plot_filename = self.media_dir / 'images/rec_hours.png'
        rec_hours_series = self.time_series['rec_hours_series']
        target_rec_hours_series = np.ones(len(rec_hours_series)) * 22
        plt.plot(date_series, target_rec_hours_series, label="Target")
        plt.plot(date_series, rec_hours_series, label="Recording hours")
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.gca().yaxis.grid()
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot ratio APP / CTM
        plot_filename = self.media_dir / 'images/app_ctm_ratio.png'
        app_ctm_series = np.array([val[1] for val in ctm_tuple_series])
        target_series = np.ones(len(app_ctm_series))
        plt.plot(date_series, target_series, label="Target")
        plt.plot(date_series, app_ctm_series, label="APP/CTM")
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
        plt.yticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5])
        plt.gca().yaxis.grid()
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

    def create_weekly_graphs(self):
        if self.prod_series and self.time_series:
            date_series = self.prod_series['date_series']
            app_series = self.prod_series['total_sp']
            ctm_tuple_series = self.prod_series['ctm_series']

        # line plot CTM and app
        plot_filename = self.media_dir / 'images/app_ctm.png'
        ctm_series = np.array([val[0] for val in ctm_tuple_series])
        plt.plot(date_series, ctm_series, label="CTM")
        plt.plot(date_series, app_series, label="APP")
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.gca().yaxis.grid()
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot of cumulative APP & CTM
        plot_filename = self.media_dir / 'images/cumul_app_ctm.png'
        app_cum_series = np.cumsum(app_series) * 0.001
        ctm_cum_series = np.cumsum(nan_array(ctm_series)) * 0.001
        plt.plot(date_series, ctm_cum_series, label="CTM")
        plt.plot(date_series, app_cum_series, label="APP")
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_CUMUL))
        plt.gca().yaxis.grid()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # pie chart of terrain distribution week
        plot_filename = self.media_dir / 'images/pie_week_terrain.png'
        terrain_labels = [val for val in self.week_terrain.keys()][:-1]
        terrain_vals = [val for val in self.week_terrain.values()][:-1]
        plt.title('Terrain - week')
        plt.pie(terrain_vals, labels=terrain_labels, autopct='%1.2f%%')
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # pie chart of terrain distribution week
        plot_filename = self.media_dir / 'images/pie_proj_terrain.png'
        terrain_labels = [val for val in self.proj_terrain.keys()][:-1]
        terrain_vals = [val for val in self.proj_terrain.values()][:-1]
        plt.title('Terrain - project')
        plt.pie(terrain_vals, labels=terrain_labels, autopct='%1.2f%%')
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()



