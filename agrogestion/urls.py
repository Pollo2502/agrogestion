from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('usuarios.urls')),
    path('compras/', include('compras.urls')),
    path('requisitor/', include('requisitor.urls')),
    path('directivo/', include('directivo.urls')),
]