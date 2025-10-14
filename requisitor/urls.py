from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout, name='logout'),
    path('panel/requisitor/requisiciones/', views.crear_requisiciones, name='crear_requisiciones'),
    path('panel/requisitor/comentarios/marcar-leidos/', views.marcar_comentarios_leidos, name='marcar_comentarios_leidos'),
]