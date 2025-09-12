from django.db import models

class Ceco(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class User(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    bloqueado = models.BooleanField(default=False)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    es_admin = models.BooleanField(default=False)
    puede_compras = models.BooleanField(default=False)
    puede_requisiciones = models.BooleanField(default=False)
    puede_aprobar = models.BooleanField(default=False)
    es_gerente = models.BooleanField(default=False)  # Nuevo permiso
    firma = models.ImageField(upload_to='firmas/', null=True, blank=True)
    ceco = models.ForeignKey(Ceco, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')  # Relación con CECO

    def __str__(self):
        return self.nombre
