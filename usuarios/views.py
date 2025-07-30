from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import User
from .crud import crear_usuario, obtener_usuarios, eliminar_usuario


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
                elif user.puede_compras:
                    return redirect('requisiciones')
                elif user.puede_requisiciones:
                    return redirect('crear_requisiciones')
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

    if request.method == 'POST':
        if 'crear_usuario' in request.POST:
            nombre = request.POST.get('nombre', '').strip()
            password = request.POST.get('password', '')
            email = request.POST.get('email', '')
            telefono = request.POST.get('telefono', '')
            permisos = request.POST.getlist('permisos')
            es_admin = 'es_admin' in permisos
            puede_compras = 'puede_compras' in permisos
            puede_requisiciones = 'puede_requisiciones' in permisos
            nuevo_usuario, error = crear_usuario(nombre, password, email, telefono, es_admin, puede_compras, puede_requisiciones)
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

    usuarios = obtener_usuarios()
    return render(request, 'control.html', {'permisos': permisos, 'usuarios': usuarios, 'user': user})


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
