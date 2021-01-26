'''  daily_report URL Configuration
'''
from django.urls import path
from daily_report.views import project_views, daily_views, weekly_views, service_views


urlpatterns = [
    path('daily_report/project_page/',
         project_views.ProjectView.as_view(), name='project_page'),
    path('daily_report/download/<str:project_name>/',
         project_views.download_pdf_workorder, name='download'),
    path('daily_report/daily_page/<int:daily_id>/',
         daily_views.DailyView.as_view(), name='daily_page'),
    path('daily_report/csr_excel_report/<int:daily_id>/',
         daily_views.csr_excel_report, name='csr_excel_report'),
    path('daily_report/weekly_page/<int:daily_id>/',
         weekly_views.WeeklyView.as_view(), name='weekly_page'),
    path('daily_report/csr_week_excel_report/<int:daily_id>/',
         weekly_views.csr_week_excel_report, name='csr_week_excel_report'),
    path('daily_report/service_page/<str:project_name>/',
         service_views.ServiceView.as_view(), name='service_page'),
    path('daily_report/monthly_services/<int:daily_id>/<int:year>/<int:month>/',
         service_views.MonthlyServiceView.as_view(), name='monthly_service_page'),
]
