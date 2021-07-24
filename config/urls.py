"""campussim URL Configuration

1. 'admin/': points to the default administrator environment provided by Django.
    This interface is accessible to only the admins of campussim.

2. include('interface.urls'): directs all the incoming requests to the applicaiton logic
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('interface.urls')),
]
