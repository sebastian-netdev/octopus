from django.contrib import admin
from django.urls import path,include
from .models import KauflandAPI
from . import views
urlpatterns = [
    path('getorders/', views.getorders),
    path('getunits/', views.getunits),
]