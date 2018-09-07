"""njr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('query2', views.query2, name='query2'),
    path('query3', views.query3, name='query3'),
    path('query4', views.query4, name='query4'),
    path('job', views.job, name='job'),
    path('make_dummy_jobs', views.make_dummy_jobs, name='make_dummy_jobs'),
    path('delete_dummy_jobs', views.delete_dummy_jobs, name='delete_dummy_jobs'),
]
