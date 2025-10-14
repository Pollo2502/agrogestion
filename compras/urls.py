from django.urls import path
from . import views

urlpatterns = [
    path('panel/compras/requisiciones/', views.requisiciones, name='requisiciones'),
    path('panel/compras/ordenes_compra/', views.ordenes_compra, name='ordenes_compra'),
    path('logout/', views.logout, name='logout'),
    path('mandar_expediente/<int:orden_id>/', views.mandar_expediente, name='mandar_expediente'),
    path('enviar_expediente/', views.enviar_expediente_a_contabilidad, name='enviar_expediente_a_contabilidad'),
    path('cargar_soporte/', views.cargar_soporte, name='cargar_soporte'),
]