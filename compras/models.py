from django.db import models
from usuarios.models import User, Ceco

class Requisicion(models.Model):
    ESTADOS = (
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('N', 'Negada'),
    )
    IMPORTANCIA_CHOICES = (
        ('N', 'Normal'),
        ('U', 'Urgente'),
    )

    codigo = models.CharField(max_length=20, unique=True)
    archivo = models.FileField(upload_to='requisiciones/')
    archivo_aprobacion = models.FileField(upload_to='aprobaciones/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_requerida = models.DateField()
    descripcion = models.TextField(max_length=500, blank=True, null=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='P')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisiciones')
    creador_req = models.CharField(max_length=100, blank=True, null=True)
    importancia = models.CharField(max_length=1, choices=IMPORTANCIA_CHOICES, default='N')
    directivo = models.ForeignKey(User, on_delete=models.PROTECT, related_name='requisiciones_recibidas', null=True, blank=True)
    ceco = models.ForeignKey(Ceco, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisiciones')
    gerente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisiciones_preaprobadas')
    estado_preaprobacion = models.CharField(max_length=1, choices=(('P', 'Pendiente'), ('A', 'Aprobada'), ('N', 'Negada')), default='P')

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return self.codigo
