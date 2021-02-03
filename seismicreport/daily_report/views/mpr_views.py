from django.http import FileResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from daily_report.report_backend import ReportInterface
from daily_report.models.daily_models import Daily
from daily_report.excel_mpr_backend import ExcelMprReport


@login_required
def mpr_excel_report(request, daily_id):
    rprt_iface = ReportInterface('')

    try:
        # get daily report from id
        day = Daily.objects.get(id=daily_id)
        project = day.project
        day, _ = rprt_iface.load_report_db(project, day.production_date)

    except Daily.DoesNotExist:
        return redirect('daily_page', 0)

    mpr_report = ExcelMprReport(day)

    # note FileResponse will close the file/ buffer - do not use with block
    f_excel = mpr_report.create_mprreport()

    return FileResponse(f_excel, as_attachment=True, filename='mpr_report.xlsx')
