from django.db import models

class Ceco(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class User(models.Model):
    TIPOS_COMPRADOR = [
        ('ferreteria', 'Ferretería'),
        ('suministros', 'Suministros'),
        ('medicina', 'Medicina'),
        ('repuestos', 'Repuestos'),
        ('insumos', 'Insumos'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    nombre_completo = models.CharField(max_length=150, null=True, blank=True)  # Nuevo campo
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    es_admin = models.BooleanField(default=False)
    puede_compras = models.BooleanField(default=False)
    puede_requisiciones = models.BooleanField(default=False)
    puede_aprobar = models.BooleanField(default=False)
    puede_contabilidad = models.BooleanField(default=False)  # permiso contabilidad
    es_gerente = models.BooleanField(default=False)  # Nuevo permiso
    firma = models.ImageField(upload_to='firmas/', null=True, blank=True)
    ceco = models.ForeignKey(Ceco, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')  # Relación con CECO
    tipo_comprador = models.CharField(max_length=50, choices=TIPOS_COMPRADOR, null=True, blank=True)  # Nuevo campo

    def __str__(self):
        return self.nombre
