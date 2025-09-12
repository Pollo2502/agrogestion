from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import User, Ceco
from .crud import crear_usuario, obtener_usuarios, eliminar_usuario, modificar_usuario, crear_ceco


def login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif user.password == password or check_password(password, user.password):
                request.session['user_id'] = user.id
                # Redirección según permisos
                if user.es_admin:
                    return redirect('panel_control')
                elif user.es_gerente:
                    return redirect('panel_gerente')  # <-- Agregado para gerente
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
        if 'crear_ceco' in request.POST:
            nombre_ceco = request.POST.get('nombre_ceco', '').strip()
            ceco, error = crear_ceco(nombre_ceco)
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'CECO creado correctamente.')
        elif 'crear_usuario' in request.POST:
            nombre = request.POST.get('nombre', '').strip()
            password = request.POST.get('password', '')
            email = request.POST.get('email', '')
            telefono = request.POST.get('telefono', '')
            ceco_id = request.POST.get('ceco')
            permisos_list = request.POST.getlist('permisos')
            es_admin = 'es_admin' in permisos_list
            puede_compras = 'puede_compras' in permisos_list
            puede_requisiciones = 'puede_requisiciones' in permisos_list
            puede_aprobar = 'puede_aprobar' in permisos_list
            es_gerente = 'es_gerente' in permisos_list
            firma = request.FILES.get('firma') if puede_aprobar else None
            nuevo_usuario, error = crear_usuario(
                nombre, password, email, telefono,
                es_admin, puede_compras, puede_requisiciones, puede_aprobar,
                es_gerente=es_gerente,
                firma=firma,
                ceco_id=ceco_id
            )
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'Usuario creado correctamente.')
        elif 'eliminar_usuario' in request.POST:
            eliminar_id = request.POST.get('eliminar_id')
            ok, error = eliminar_usuario(eliminar_id)
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'Usuario eliminado correctamente.')
        elif 'editar_usuario' in request.POST:
            editar_id = request.POST.get('editar_id')
            nombre = request.POST.get('nombre', None)
            email = request.POST.get('email', None)
            telefono = request.POST.get('telefono', None)
            ceco_id = request.POST.get('ceco')
            permisos_list = request.POST.getlist('permisos')
            es_admin = 'es_admin' in permisos_list
            puede_compras = 'puede_compras' in permisos_list
            puede_requisiciones = 'puede_requisiciones' in permisos_list
            puede_aprobar = 'puede_aprobar' in permisos_list
            es_gerente = 'es_gerente' in permisos_list
            firma = request.FILES.get('firma') if puede_aprobar else None

            user, error = modificar_usuario(
                editar_id,
                nombre=nombre,
                email=email,
                telefono=telefono,
                es_admin=es_admin,
                puede_compras=puede_compras,
                puede_requisiciones=puede_requisiciones,
                puede_aprobar=puede_aprobar,
                es_gerente=es_gerente,
                firma=firma,
                ceco_id=ceco_id
            )
            if error:
                messages.error(request, error)
            else:
                messages.success(request, 'Usuario modificado correctamente.')
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
    return permisos

def logout(request):
    request.session.flush()
    return redirect('login')
