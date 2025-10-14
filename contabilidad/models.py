from django.db import models
from usuarios.models import User
from compras.models import OrdenCompra


class SolicitudAnticipo(models.Model):
    ESTADOS = (
        ('P', 'Pendiente'),
        ('E', 'En Proceso'),
        ('F', 'Finalizado'),
    )

    orden = models.OneToOneField(OrdenCompra, on_delete=models.CASCADE, related_name='solicitud_anticipo')
    contabilidad = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_anticipo')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='P')
    archivo_zip = models.FileField(upload_to='expedientes/', null=True, blank=True)
    tracking_text = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Solicitud {self.orden.requisicion.codigo} -> {self.contabilidad.nombre if self.contabilidad else 'Sin asignar'}"
from django.db import models

# Create your models here.
