from django.urls import path
from . import views

urlpatterns = [
        path('panel/control/', views.aprobar_requisiciones, name='aprobar_requisiciones'),
        path('logout/', views.logout, name='logout'),
    ]