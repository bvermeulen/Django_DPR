'''  daily_report URL Configuration
'''
from django.urls import path
from daily_report.views import project_views, daily_views


urlpatterns = [
    path('daily_report/project_page/',
         project_views.ProjectView.as_view(), name='project_page'),
    path('daily_report/download/<str:project_name>/',
         project_views.download_pdf_workorder, name='download'),
    path('daily_report/service_page/<str:project_name>/',
         project_views.ServiceView.as_view(), name='service_page'),
    path('daily_report/daily_page/<int:daily_id>/',
         daily_views.DailyView.as_view(), name='daily_page'),
    path('daily_report/monthly_services/<int:daily_id>/<int:year>/<int:month>/',
         daily_views.MonthlyServiceView.as_view(), name='monthly_service_page'),
]
