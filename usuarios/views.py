from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .crud import crear_usuario, obtener_usuarios, eliminar_usuario, modificar_usuario, crear_ceco
from .models import User, Ceco


def login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif user.password == password or check_password(password, user.password):
                request.session['user_id'] = user.pk
                # Redirección según permisos
                if user.es_admin:
                    return redirect('panel_control')
                elif user.es_gerente:
                    return redirect('panel_gerente')
                elif user.puede_contabilidad:
                    return redirect('solicitud_anticipo')  # acceso contabilidad
                elif user.puede_compras:
                    return redirect('requisiciones')
                elif user.puede_requisiciones:
                    return redirect('crear_requisiciones')
                elif user.puede_aprobar:
                    return redirect('aprobar_requisiciones')
                else:
                    messages.error(request, 'No tiene permisos asignados')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'login.html')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'login.html')

    return render(request, 'login.html')


def panel_control(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    permisos = get_permisos(user)

    if not user.es_admin:
        messages.error(request, 'No tiene permisos de administrador')
        return redirect('login')

    cecos = Ceco.objects.all()  # <-- Agrega esto

    if request.method == 'POST':
        # Crear usuario
        if 'crear_usuario' in request.POST:
            nombre = request.POST.get('nombre', '').strip()
            nombre_completo = request.POST.get('nombre_completo', '').strip()
            password = request.POST.get('password', '')
            email = request.POST.get('email', '')
            telefono = request.POST.get('telefono', '')
            ceco_id = request.POST.get('ceco')
            permisos_list = request.POST.getlist('permisos')
            es_admin = 'es_admin' in permisos_list
            puede_compras = 'puede_compras' in permisos_list
            puede_requisiciones = 'puede_requisiciones' in permisos_list
            puede_aprobar = 'puede_aprobar' in permisos_list
            puede_contabilidad = 'puede_contabilidad' in permisos_list
            es_gerente = 'es_gerente' in permisos_list
            # allow firma upload if user can approve, is gerente, can requisitions or can compras
            firma = request.FILES.get('firma') if (puede_aprobar or es_gerente or puede_requisiciones or puede_compras) else None
            tipo_comprador = request.POST.get('tipo_comprador') if puede_compras else None

            nuevo_usuario, error = crear_usuario(
                nombre, nombre_completo, password, email, telefono,
                es_admin=es_admin, puede_compras=puede_compras,
                puede_requisiciones=puede_requisiciones,
                puede_aprobar=puede_aprobar, es_gerente=es_gerente,
                firma=firma, ceco_id=ceco_id, tipo_comprador=tipo_comprador,
                puede_contabilidad=puede_contabilidad
            )
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'Usuario creado correctamente.')

        # Editar usuario
        elif 'editar_usuario' in request.POST:
            editar_id = request.POST.get('editar_id')
            nombre = request.POST.get('nombre', None)
            nombre_completo = request.POST.get('nombre_completo', None)
            email = request.POST.get('email', None)
            telefono = request.POST.get('telefono', None)
            ceco_id = request.POST.get('ceco')
            permisos_list = request.POST.getlist('permisos')
            es_admin = 'es_admin' in permisos_list
            puede_compras = 'puede_compras' in permisos_list
            puede_requisiciones = 'puede_requisiciones' in permisos_list
            puede_aprobar = 'puede_aprobar' in permisos_list
            puede_contabilidad = 'puede_contabilidad' in permisos_list
            es_gerente = 'es_gerente' in permisos_list
            # allow firma upload for edit when any of the firma-related permisos are present
            firma = request.FILES.get('firma') if (puede_aprobar or es_gerente or puede_requisiciones or puede_compras) else None
            tipo_comprador = request.POST.get('tipo_comprador') if puede_compras else None

            user, error = modificar_usuario(
                editar_id,
                nombre=nombre,
                nombre_completo=nombre_completo,
                email=email,
                telefono=telefono,
                es_admin=es_admin,
                puede_compras=puede_compras,
                puede_requisiciones=puede_requisiciones,
                puede_aprobar=puede_aprobar,
                puede_contabilidad=puede_contabilidad,
                es_gerente=es_gerente,
                firma=firma,
                ceco_id=ceco_id,
                tipo_comprador=tipo_comprador
            )
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'Usuario modificado correctamente.')

        # Eliminar usuario
        elif 'eliminar_usuario' in request.POST:
            eliminar_id = request.POST.get('eliminar_id')
            if not eliminar_id:
                messages.error(request, 'ID de usuario no proporcionado.')
            else:
                try:
                    result = eliminar_usuario(eliminar_id)
                    # soporta distintas firmas de eliminar_usuario (tuple o None/exception)
                    if isinstance(result, tuple):
                        obj, err = result
                        if err:
                            messages.error(request, err)
                        else:
                            messages.success(request, 'Usuario eliminado correctamente.')
                    else:
                        messages.success(request, 'Usuario eliminado correctamente.')
                except Exception as e:
                    messages.error(request, f'Error al eliminar usuario: {e}')
    usuarios = obtener_usuarios()
    return render(request, 'control.html', {'permisos': permisos, 'usuarios': usuarios, 'user': user, 'cecos': cecos})


def get_permisos(user):
    permisos = []
    if user.es_admin:
        permisos.append('usuarios')
    if user.puede_compras:
        permisos.append('compras')
        permisos.append('ordenes_compra')
    if user.puede_requisiciones:
        permisos.append('crear_requisiciones')
    if user.puede_aprobar:
        permisos.append('aprobar_requisiciones')
    if user.puede_contabilidad:
        permisos.append('contabilidad')
    return permisos

def logout(request):
    request.session.flush()
    return redirect('login')
