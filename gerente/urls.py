from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.panel_gerente, name='panel_gerente'),
]