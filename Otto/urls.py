from django.contrib import admin
from django.urls import path,include

from . import views
urlpatterns = [
    path('gettoken/', views.gettoken),
    path('getoffers/', views.getoffers),
    path('findproducts/', views.findproducts),
    path('getorders/', views.getorders),
]