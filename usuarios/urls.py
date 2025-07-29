from django.urls import path
from . import views

urlpatterns = [
        path('', views.login, name='login'),
        path('panel/control/', views.panel_control, name='panel_control'),
        path('logout/', views.logout, name='logout'),
    ]