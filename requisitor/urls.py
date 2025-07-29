from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout, name='logout'),
    path('panel/requisitor/requisiciones/', views.crear_requisiciones, name='crear_requisiciones'),
]