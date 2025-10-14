from django.db import models


class RequisicionComentario(models.Model):
    requisicion = models.ForeignKey('Requisicion', on_delete=models.CASCADE, related_name='comentarios')
    # Referencia explícita al modelo de usuario del proyecto
    autor = models.ForeignKey('usuarios.User', on_delete=models.SET_NULL, null=True, blank=True)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Comentario #{self.id} - {self.requisicion.codigo if self.requisicion else 'sin-requisicion'}"
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
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisiciones_creadas')  # Usuario que crea la requisición
    usuario_compras = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisiciones_compras', null=True, blank=True)  # Usuario encargado de compras
    importancia = models.CharField(max_length=1, choices=IMPORTANCIA_CHOICES, default='N')
    directivo = models.ForeignKey(User, on_delete=models.PROTECT, related_name='requisiciones_recibidas', null=True, blank=True)
    ceco = models.ForeignKey(Ceco, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisiciones')
    gerente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisiciones_preaprobadas')
    estado_preaprobacion = models.CharField(max_length=1, choices=(('P', 'Pendiente'), ('A', 'Aprobada'), ('N', 'Negada')), default='P')
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return self.codigo


class OrdenCompra(models.Model):
    ESTADOS = (
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('N', 'Rechazada'),
    )

    requisicion = models.OneToOneField(Requisicion, on_delete=models.CASCADE, related_name='orden_compra')
    archivo_orden = models.FileField(upload_to='ordenes_compra/')
    archivo_cuadro_comparativo = models.FileField(upload_to='cuadros_comparativos/')
    archivo_presupuesto = models.FileField(upload_to='presupuestos/')
    # nuevo: documento de soporte (nota de recepción o factura)
    TIPO_SOPORTE = (
        ('nota', 'Nota de recepción'),
        ('factura', 'Factura'),
    )
    archivo_soporte = models.FileField(upload_to='soportes/', null=True, blank=True)
    tipo_soporte = models.CharField(max_length=10, choices=TIPO_SOPORTE, null=True, blank=True)
    estado = models.CharField(max_length=1, choices=ESTADOS, default='P')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)  # Nuevo campo

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Orden de Compra para {self.requisicion.codigo}"
