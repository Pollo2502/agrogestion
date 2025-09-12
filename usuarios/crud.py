from .models import User, Ceco
from django.contrib.auth.hashers import make_password

def crear_usuario(nombre, password, email=None, telefono=None, es_admin=False, puede_compras=False, puede_requisiciones=False, puede_aprobar=False, es_gerente=False, firma=None, ceco_id=None):
    if User.objects.filter(nombre=nombre).exists():
        return None, "El nombre de usuario ya existe."
    if email and User.objects.filter(email=email).exists():
        return None, "El email ya está registrado."
    ceco = Ceco.objects.get(id=ceco_id) if ceco_id else None
    hashed_password = make_password(password)
    user = User(
        nombre=nombre,
        password=hashed_password,
        email=email if email else None,
        telefono=telefono if telefono else None,
        es_admin=es_admin,
        puede_compras=puede_compras,
        puede_requisiciones=puede_requisiciones,
        puede_aprobar=puede_aprobar,
        es_gerente=es_gerente,
        firma=firma if puede_aprobar and firma else None,
        ceco=ceco,
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

def modificar_usuario(user_id, nombre=None, email=None, telefono=None, es_admin=None, puede_compras=None, puede_requisiciones=None, puede_aprobar=None, es_gerente=None, firma=None, ceco_id=None):
    try:
        user = User.objects.get(id=user_id)
        if nombre is not None and nombre != user.nombre:
            if User.objects.exclude(id=user_id).filter(nombre=nombre).exists():
                return None, "El nombre de usuario ya existe."
            user.nombre = nombre
        if email is not None and email != user.email:
            if email and User.objects.exclude(id=user_id).filter(email=email).exists():
                return None, "El email ya está registrado."
            user.email = email
        if telefono is not None:
            user.telefono = telefono
        if es_admin is not None:
            user.es_admin = es_admin
        if puede_compras is not None:
            user.puede_compras = puede_compras
        if puede_requisiciones is not None:
            user.puede_requisiciones = puede_requisiciones
        if puede_aprobar is not None:
            user.puede_aprobar = puede_aprobar
        if es_gerente is not None:
            user.es_gerente = es_gerente
        if ceco_id is not None:
            user.ceco = Ceco.objects.get(id=ceco_id)
        if puede_aprobar and firma is not None:
            user.firma = firma
        elif not puede_aprobar:
            if user.firma:
                user.firma.delete(save=False)
        user.save()
        return user, None
    except User.DoesNotExist:
        return None, "Usuario no encontrado."
    except Ceco.DoesNotExist:
        return None, "CECO no encontrado."

def crear_ceco(nombre):
    if Ceco.objects.filter(nombre=nombre).exists():
        return None, "El CECO ya existe."
    ceco = Ceco(nombre=nombre)
    ceco.save()
    return ceco, None