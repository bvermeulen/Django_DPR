''' module to manage weekly report backend tasks
'''
from datetime import timedelta
import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from daily_report.models.daily_models import Person, Daily
from daily_report.models.weekly_models import Weekly
from daily_report.report_backend import ReportInterface
from seismicreport.vars import WEEKDAYS, WEEKS
from seismicreport.utils.plogger import timed, Logger


logger = Logger.getlogger()


class WeekInterface:

    rprt_iface = ReportInterface('')

    def __init__(self, media_dir):
        self.media_dir = media_dir

    @staticmethod
    def get_week_values(day):
        if not day:
            return {}

        start_week = day.production_date - timedelta(WEEKDAYS-1)
        end_week = day.production_date

        try:
            week = day.project.weeklies.get(week_report_date=day.production_date)
            initial_week_form = {
                'week_start_date': start_week,
                'week_report_date': week.week_report_date,
                'proj_name': week.project.project_name,
                'proj_vps': day.project.planned_vp,
                'proj_area': day.project.planned_area,
                'proj_start': day.project.planned_start_date,
                'proj_crew': day.project.crew_name,
                'author': [week.author.id],
                'csr_week_comment': week.csr_week_comment,
            }

        except (AttributeError, ObjectDoesNotExist):
            initial_week_form = {
                'week_start_date': start_week,
                'week_report_date': end_week,
                'proj_name': day.project.project_name,
                'proj_vps': day.project.planned_vp,
                'proj_area': day.project.planned_area,
                'proj_start': day.project.planned_start_date,
                'proj_crew': day.project.crew_name,
                'author': [],
                'csr_week_comment': '',
            }

        return initial_week_form

    @staticmethod
    def update_week_report(day, week_comment, author_id):
        try:
            week = Weekly.objects.get(
                project=day.project, week_report_date=day.production_date)

        except Weekly.DoesNotExist:
            week = Weekly.objects.create(
                project=day.project, week_report_date=day.production_date)

        week.csr_week_comment = week_comment
        try:
            week.author = Person.objects.get(id=author_id)

        except (ValueError, Person.DoesNotExist):
            pass

        week.save()

    @staticmethod
    def delete_week_report(day):
        try:
            week = Weekly.objects.get(
                project=day.project, week_report_date=day.production_date)

        except Weekly.DoesNotExist:
            return

        week.delete()


    @timed(logger, print_log=True)
    def collate_weekdata(self, report_day):

        # get the production figures for the days in the week
        days = {}
        project = report_day.project
        start_date = report_day.production_date - timedelta(days=WEEKDAYS-1)
        for wd in reversed(range(0, WEEKDAYS)):
            report_date = start_date + timedelta(days=wd)
            days[wd] = {}
            days[wd]['date'] = report_date
            try:
                day = Daily.objects.get(project=project, production_date=report_date)
            except Daily.DoesNotExist:
                day = None
            (
                _,
                days[wd]['prod'],
                days[wd]['times'],
                days[wd]['rcvr'],
                _
            ) = self.rprt_iface.calc_totals(day)

            try:
                days[wd]['prod']['day_vp_hour'] = (round(
                    days[wd]['prod']['day_total'] /
                    days[wd]['times']['day_rec_time']))

            except (ValueError, KeyError):
                days[wd]['prod']['day_vp_hour'] = np.nan

        # get the weekly production figures for the 6 weeks before
        weeks = {}
        start_date = report_day.production_date - timedelta(days=(WEEKS-1)*WEEKDAYS)
        for wk in range(0, WEEKS):
            report_date = start_date + timedelta(days=WEEKDAYS*wk)
            weeks[wk] = {}
            weeks[wk]['dates'] = (report_date - timedelta(days=(WEEKDAYS-1)), report_date)
            try:
                day = Daily.objects.get(project=project, production_date=report_date)
            except Daily.DoesNotExist:
                # skip this week
                day = None

            (
                _,
                weeks[wk]['prod'],
                weeks[wk]['times'],
                weeks[wk]['rcvr'],
                _
            ) = self.rprt_iface.calc_totals(day)

            try:
                weeks[wk]['prod']['week_vp_hour'] = (round(
                    weeks[wk]['prod']['week_total'] /
                    weeks[wk]['times']['week_rec_time']))

            except (ValueError, KeyError):
                weeks[wk]['prod']['week_vp_hour'] = np.nan

        return days, weeks
