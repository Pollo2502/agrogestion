from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('usuarios.urls')),
    path('compras/', include('compras.urls')),
    path('requisitor/', include('requisitor.urls')),
    path('directivo/', include('directivo.urls')),
    path('gerente/', include('gerente.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)