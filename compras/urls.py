from django.urls import path
from . import views

urlpatterns = [
    path('panel/compras/requisiciones/', views.requisiciones, name='requisiciones'),
    path('panel/compras/ordenes_compra/', views.ordenes_compra, name='ordenes_compra'),
    path('logout/', views.logout, name='logout'),
]