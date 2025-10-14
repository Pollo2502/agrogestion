from django.urls import path
from . import views

urlpatterns = [
        path('panel/control/', views.aprobar_requisiciones, name='aprobar_requisiciones'),
        path('panel/compras/', views.aprobar_compras, name='aprobar_compras'),
        path('panel/directivo/', views.panel_directivo, name='panel_directivo'),
        path('logout/', views.logout, name='logout'),
    ]