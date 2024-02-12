from django.contrib import admin
from django.urls import path,include

from . import views
urlpatterns = [
    path('validateorders/', views.validateorders),
    path('registerorders/', views.registerorders),
    path('getorders/', views.getorders),
    path('getstocks/', views.getstocks),
    path('getproducts/', views.getproducts),
    path('getorderfields/', views.getorderextrafields),
    path('setassent/', views.setassent),
]