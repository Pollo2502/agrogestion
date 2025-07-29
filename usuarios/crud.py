from .models import User
from django.contrib.auth.hashers import make_password

def crear_usuario(nombre, password, email=None, telefono=None, es_admin=False, puede_compras=False, puede_requisiciones=False):
    if User.objects.filter(nombre=nombre).exists():
        return None, "El nombre de usuario ya existe."
    if email and User.objects.filter(email=email).exists():
        return None, "El email ya está registrado."
    hashed_password = make_password(password)
    user = User(
        nombre=nombre,
        password=hashed_password,
        email=email if email else None,
        telefono=telefono if telefono else None,
        es_admin=es_admin,
        puede_compras=puede_compras,
        puede_requisiciones=puede_requisiciones,
    )
    user.save()
    return user, None

def obtener_usuarios():
    return User.objects.all()

def eliminar_usuario(user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return True, None
    except User.DoesNotExist:
        return False, "Usuario no encontrado."