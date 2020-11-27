import numpy as np
import matplotlib.pyplot as plt
from daily_report.models.daily_models import Daily, SourceProduction, TimeBreakdown, HseWeather, ToolBox
from daily_report.models.project_models import Project, Service, ServiceTask, TaskQuantity
project = Project.objects.get(project_name='19GL')
daily = Daily.objects.get(production_date='2020-5-1', project=project)
bdz = Service.objects.get(project=project, service_contract='BDZ')
mob = ServiceTask.objects.get(service=bdz, task_name='mob/demob')

prod = SourceProduction.objects.get(daily=daily, sourcetype=daily.project.sourcetypes.get(sourcetype_name='vibe_25m'))
from daily_report.report_backend import ReportInterface
report = ReportInterface('..\media')
p, t = report.calc_totals(daily)

vp_query = SourceProduction.objects.filter(daily__production_date__lte=daily.production_date).order_by('daily__production_date')
date_series = [val.daily.production_date for val in vp_query]
vp_t1_series = [val['vp_terrain_1_flat'] for val in vp_query.values()]
vp_t2_series = [val['vp_terrain_2_rough'] for val in vp_query.values()]
vp_t3_series = [val['vp_terrain_3_facilities'] for val in vp_query.values()]
vp_t4_series = [val['vp_terrain_4_dunes'] for val in vp_query.values()]
vp_t5_series = [val['vp_terrain_5_sabkha'] for val in vp_query.values()]
terrain_series = list(zip(vp_t1_series, vp_t2_series, vp_t3_series, vp_t4_series, vp_t5_series))
vp_totals_series = [np.nansum(vals) for vals in terrain_series]
vp_skips_series = [val['skips'] for val in vp_query.values()]
#fig = plt.figure()
# p1 = plt.bar(date_series, vp_t1_series, label="Flat")
# bottom = vp_t1_series
# p2 = plt.bar(date_series, vp_t2_series, bottom=bottom, label="Rough")
# bottom = np.add(bottom, vp_t2_series).tolist()
# p3 = plt.bar(date_series, vp_t3_series, bottom=bottom, label="Facilities")
# bottom = np.add(bottom, vp_t3_series).tolist()
# p4 = plt.bar(date_series, vp_t4_series, bottom=bottom, label="Dunes")
# bottom = np.add(bottom, vp_t4_series).tolist()
# p5 = plt.bar(date_series, vp_t5_series, bottom=bottom, label="Sabkha")
# plt.plot(date_series, vp_totals_series)
t1_cum = np.cumsum(vp_t1_series)
t2_cum = np.cumsum(vp_t2_series)
t3_cum = np.cumsum(vp_t3_series)
t4_cum = np.cumsum(vp_t4_series)
t5_cum = np.cumsum(vp_t5_series)
base = np.zeros(len(date_series))
if any(t1_cum):
    base += t1_cum
    p1 = plt.plot(date_series, base, label="Flat")

if any(t2_cum):
    base += t2_cum
    p2 = plt.plot(date_series, base, label="Rough")

if any(t3_cum):
    base += t3_cum
    p3 = plt.plot(date_series, base, label="Facilities")

if any(t4_cum):
    base += t4_cum
    p4 = plt.plot(date_series, base, label="Dunes")

if any(t5_cum):
    base += t5_cum
    p5 = plt.plot(date_series, base, label="Sabkha")

plt.xticks(rotation=70)
plt.legend()
plt.tight_layout()
plt.show()
