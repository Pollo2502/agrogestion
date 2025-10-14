from django.urls import path
from . import views

urlpatterns = [
    path('solicitud_anticipo/', views.solicitud_anticipo, name='solicitud_anticipo'),
]