''' module for creating graphs
'''
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from seismicreport.vars import TICK_SPACING_PROD, TICK_SPACING_CUMUL, TICK_DATE_FORMAT
from seismicreport.utils.utils_funcs import nan_array
from seismicreport.utils.plogger import Logger, timed

matplotlib.use('Agg')
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
            assert len(date_series) == len(self.prod_series['sp_t1_series']), \
                'length date en terrain series must be equal'

        else:
            return

        # stacked bar plot of daily production
        t1_series = self.prod_series['sp_t1_series'] * 0.001
        t2_series = self.prod_series['sp_t2_series'] * 0.001
        t3_series = self.prod_series['sp_t3_series'] * 0.001
        t4_series = self.prod_series['sp_t4_series'] * 0.001
        t5_series = self.prod_series['sp_t5_series'] * 0.001
        base = np.zeros(len(date_series))

        width = 1
        plot_filename = self.media_dir / 'images/daily_prod.png'

        if any(t1_series):
            plt.bar(date_series, t1_series, width, label="Flat", zorder=2)
            base += t1_series

        if any(t2_series):
            plt.bar(date_series, t2_series, width, bottom=base, label="Rough", zorder=3)
            base += t2_series

        if any(t3_series):
            plt.bar(
                date_series, t3_series, width, bottom=base, label="Facilities", zorder=4)
            base += t3_series

        if any(t4_series):
            plt.bar(date_series, t4_series, width, bottom=base, label="Dunes", zorder=6)
            base += t4_series

        if any(t5_series):
            plt.bar(date_series, t5_series, width, bottom=base, label="Sabkha", zorder=5)

        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_PROD))
        plt.gca().yaxis.grid(zorder=1)
        plt.tick_params(axis='both', labelsize=7)
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
            plt.plot(date_series, base, label="Flat", zorder=2)

        if any(t2_cum):
            base += t2_cum
            plt.plot(date_series, base, label="Rough", zorder=3)

        if any(t3_cum):
            base += t3_cum
            plt.plot(date_series, base, label="Facilities", zorder=4)

        if any(t4_cum):
            base += t4_cum
            plt.plot(date_series, base, label="Dunes", zorder=6)

        if any(t5_cum):
            base += t5_cum
            plt.plot(date_series, base, label="Sabkha", zorder=5)

        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_CUMUL))
        plt.gca().yaxis.grid(zorder=1)
        plt.tick_params(axis='both', labelsize=7)
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot recording hours
        plot_filename = self.media_dir / 'images/rec_hours.png'
        rec_hours_series = self.time_series['rec_hours_series']
        target_rec_hours_series = np.ones(len(rec_hours_series)) * self.mpr_rec_hours
        plt.plot(date_series, target_rec_hours_series, label="Target", zorder=2)
        plt.plot(date_series, rec_hours_series, label="Recording hours", zorder=3)
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.gca().yaxis.grid(zorder=1)
        plt.tick_params(axis='both', labelsize=7)
        plt.xticks(rotation=70)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot ratio APP / CTM
        plot_filename = self.media_dir / 'images/app_ctm_ratio.png'
        appctm_series = self.prod_series['appctm_series']
        target_series = np.ones(len(appctm_series))
        plt.plot(date_series, target_series, label="Target", zorder=2)
        plt.plot(date_series, appctm_series, label="APP/CTM", zorder=3)
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
        plt.gca().yaxis.grid(zorder=1)
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.yticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5])
        plt.tick_params(axis='both', labelsize=7)
        plt.xticks(rotation=70)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

    @timed(logger, print_log=True)
    def create_weekly_graphs(self):
        if self.prod_series and self.time_series:
            date_series = self.prod_series['date_series']
            app_series = self.prod_series['total_sp_series']

        # line plot CTM and app
        plot_filename = self.media_dir / 'images/app_ctm.png'
        ctm_series = self.prod_series['ctm_series']
        plt.plot(date_series, ctm_series, label="CTM", zorder=2)
        plt.plot(date_series, app_series, label="APP", zorder=3)
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.gca().yaxis.grid(zorder=1)
        plt.tick_params(axis='both', labelsize=7)
        plt.xticks(rotation=70)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot of cumulative APP & CTM
        plot_filename = self.media_dir / 'images/cumul_app_ctm.png'
        app_cum_series = np.cumsum(app_series) * 0.001
        ctm_cum_series = np.cumsum(nan_array(ctm_series)) * 0.001
        plt.plot(date_series, ctm_cum_series, label="CTM", zorder=2)
        plt.plot(date_series, app_cum_series, label="APP", zorder=3)
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.gca().yaxis.grid(zorder=1)
        plt.xticks(rotation=70)
        plt.tick_params(axis='both', labelsize=7)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_CUMUL))
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # pie chart of terrain distribution week
        plot_filename = self.media_dir / 'images/pie_week_terrain.png'
        terrain_labels = [val for val in self.week_terrain.keys()][:-1]
        terrain_vals = nan_array([val for val in self.week_terrain.values()][:-1])
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

        # pie chart of recording times
        plot_filename = self.media_dir / 'images/pie_week_times.png'

        # get 18, 19, 20 element for the 6th (which is the current) week
        time_labels = [val for val in self.weeks_times['header'][18:]]
        time_vals = nan_array([val for val in self.weeks_times[5][18:]])
        plt.title('Weekly time breakdown')
        plt.pie(time_vals, labels=time_labels, autopct='%1.2f%%')
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # bar chart of weekly production
        plot_filename = self.media_dir / 'images/bar_week_production.png'
        date_series = [val[0].replace(' ', '\n') for val in self.weeks_prod.values()
            if val[0] != 'Week']
        prod_series = nan_array([val[1] / 1000 for val in self.weeks_prod.values()
            if not isinstance(val[1], str)])
        plt.bar(date_series, prod_series, zorder=2)
        for i, val in enumerate(prod_series):
            plt.annotate(
                f'{str(round(val))}k', xy=(date_series[i], prod_series[i]),
                ha='center', va='bottom')
        plt.grid(axis='y', zorder=1)
        plt.title('Weekly production')
        plt.tick_params(axis='both', labelsize=7)
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # bar chart of daily production
        plot_filename = self.media_dir / 'images/bar_day_production.png'
        date_series = [val[0] for val in self.days_prod.values()
            if val[0] != 'Day']
        prod_series = nan_array([val[1] for val in self.days_prod.values()
            if not isinstance(val[1], str)])
        plt.bar(date_series, prod_series, zorder=2)
        for i, val in enumerate(prod_series):
            plt.annotate(
                f'{val:,}', xy=(date_series[i], prod_series[i]),
                ha='center', va='bottom')
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.grid(zorder=1)
        plt.title('Daily production')
        plt.tick_params(axis='both', labelsize=7)
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # bar chart daily recording hours
        plot_filename = self.media_dir / 'images/bar_day_rechours.png'
        rec_series = nan_array([val[2] for val in self.days_prod.values()
            if not isinstance(val[2], str)])
        plt.bar(date_series, rec_series, zorder=2)
        for i, val in enumerate(rec_series):
            plt.annotate(
                f'{val:.2f}', xy=(date_series[i], rec_series[i]),
                ha='center', va='bottom')
        ax = plt.gca()
        ax.set_ylim(10, 25)
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
        ax.yaxis.grid(zorder=1)
        plt.title('Daily recording hours')
        plt.tick_params(axis='both', labelsize=7)
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # bar chart daily VPs per hour
        plot_filename = self.media_dir / 'images/bar_day_vphr.png'
        vphr_series = nan_array([val[3] for val in self.days_prod.values()
            if not isinstance(val[3], str)])
        plt.bar(date_series, vphr_series, zorder=2)
        for i, val in enumerate(vphr_series):
            plt.annotate(
                f'{val:.0f}', xy=(date_series[i], vphr_series[i]),
                ha='center', va='bottom')
        ax = plt.gca()
        ax.set_ylim(500, 1600)
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
        ax.yaxis.grid(zorder=1)
        plt.title('Daily VP per hour')
        plt.tick_params(axis='both', labelsize=7)
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()
