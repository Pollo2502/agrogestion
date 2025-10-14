from .models import User, Ceco
from django.contrib.auth.hashers import make_password

def crear_usuario(nombre, nombre_completo, password, email=None, telefono=None,
                  es_admin=False, puede_compras=False, puede_requisiciones=False,
                  puede_aprobar=False, es_gerente=False, firma=None, ceco_id=None,
                  tipo_comprador=None, puede_contabilidad=False):
    if User.objects.filter(nombre=nombre).exists():
        return None, "El nombre de usuario ya existe."
    if email and User.objects.filter(email=email).exists():
        return None, "El email ya está registrado."
    ceco = Ceco.objects.get(id=ceco_id) if ceco_id else None
    hashed_password = make_password(password)
    # Assign firma if the user can approve, is gerente, can make requisitions or is a comprador
    assign_firma = None
    if firma and (puede_aprobar or es_gerente or puede_requisiciones or puede_compras):
        assign_firma = firma

    user = User(
        nombre=nombre,
        nombre_completo=nombre_completo,
        password=hashed_password,
        email=email if email else None,
        telefono=telefono if telefono else None,
        es_admin=es_admin,
        puede_compras=puede_compras,
        puede_requisiciones=puede_requisiciones,
        puede_aprobar=puede_aprobar,
        puede_contabilidad=puede_contabilidad,
        es_gerente=es_gerente,
        firma=assign_firma,
        ceco=ceco,
        tipo_comprador=tipo_comprador if puede_compras else None
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

def modificar_usuario(user_id, nombre=None, nombre_completo=None, email=None, telefono=None,
                      es_admin=None, puede_compras=None, puede_requisiciones=None,
                      puede_aprobar=None, es_gerente=None, firma=None, ceco_id=None,
                      tipo_comprador=None, puede_contabilidad=None):
    try:
        user = User.objects.get(id=user_id)
        if nombre is not None and nombre != user.nombre:
            if User.objects.exclude(id=user_id).filter(nombre=nombre).exists():
                return None, "El nombre de usuario ya existe."
            user.nombre = nombre
        if nombre_completo is not None:
            user.nombre_completo = nombre_completo
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
            if not puede_compras:
                user.tipo_comprador = None
        # solo asignar tipo_comprador si el usuario es comprador
        if tipo_comprador is not None and (puede_compras or user.puede_compras):
            user.tipo_comprador = tipo_comprador
        if puede_contabilidad is not None:
            user.puede_contabilidad = puede_contabilidad
        if puede_requisiciones is not None:
            user.puede_requisiciones = puede_requisiciones
        if puede_aprobar is not None:
            user.puede_aprobar = puede_aprobar
        if es_gerente is not None:
            user.es_gerente = es_gerente
        if ceco_id is not None:
            user.ceco = Ceco.objects.get(id=ceco_id)
        # Update firma: keep it if the user has any permission that allows firma (aprobar, gerente, requisitor, compras)
        permiso_firma_actual = user.puede_aprobar or user.es_gerente or user.puede_requisiciones or user.puede_compras
        permiso_firma_nuevo = False
        if puede_aprobar is not None:
            permiso_firma_nuevo = puede_aprobar or permiso_firma_nuevo
        if es_gerente is not None:
            permiso_firma_nuevo = es_gerente or permiso_firma_nuevo
        if puede_requisiciones is not None:
            permiso_firma_nuevo = puede_requisiciones or permiso_firma_nuevo
        if puede_compras is not None:
            permiso_firma_nuevo = puede_compras or permiso_firma_nuevo

        # If a new firma file is provided and the resulting permissions include firma, set it
        if firma is not None and permiso_firma_nuevo:
            # replace existing file (Django will handle storage)
            if user.firma:
                user.firma.delete(save=False)
            user.firma = firma
        else:
            # If the resulting permissions do NOT include firma, remove existing signature
            if not permiso_firma_nuevo:
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