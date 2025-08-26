from django.contrib import admin
from django.urls import path
from jobs.views import job_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', job_list, name='job_list'),
]
