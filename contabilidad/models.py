from django.db import models
from usuarios.models import User
from compras.models import OrdenCompra
from django.utils.timezone import now


class SolicitudAnticipo(models.Model):
    ESTADOS = (
        ('E', 'En Proceso'),
        ('F', 'Finalizado'),
    )

    orden = models.OneToOneField(OrdenCompra, on_delete=models.CASCADE, related_name='solicitud_anticipo')
    contabilidad = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_contabilidad')
    estado = models.CharField(max_length=1, choices=ESTADOS, default='E')  # Estado de la solicitud
    tracking_text = models.TextField(null=True, blank=True)  # Texto de tracking
    archivo_zip = models.FileField(upload_to='expedientes/', null=True, blank=True)  # Archivo ZIP relacionado
    portada_pdf = models.FileField(upload_to='expedientes/portadas/', null=True, blank=True)  # Portada generada (PDF)
    # Trazabilidad: marcar si el ZIP fue descargado y por quién (requisito para crear portada)
    zip_descargado = models.BooleanField(default=False)
    zip_descargado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='zips_descargados')
    zip_descargado_fecha = models.DateTimeField(null=True, blank=True)
    fecha_envio = models.DateTimeField(default=now)  # Set a default value for existing rows
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Fecha de creación
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # Fecha de última actualización

    class Meta:
        ordering = ['-fecha_creacion']  # Order by fecha_creacion in descending order

    def __str__(self):
        return f"Solicitud Anticipo - Orden: {self.orden.requisicion.codigo}"
