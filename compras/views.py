from django.shortcuts import render, redirect
from django.contrib import messages
from usuarios.models import User  # Importa el modelo User desde la app usuarios
from .models import Requisicion


# Puedes importar get_permisos si lo tienes en usuarios.views
def get_permisos(user):
    permisos = []
    if user.es_admin:
        permisos.append('usuarios')
    if user.puede_compras:
        permisos.append('compras')
        permisos.append('ordenes_compra')
    if user.puede_requisiciones:
        permisos.append('crear_requisiciones')
    return permisos

def requisiciones(request):
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
    requisiciones = Requisicion.objects.all()

    # Puedes agregar más lógica aquí si lo necesitas

    return render(request, 'requisiciones.html', {'permisos': permisos, 'user': user, 'requisiciones': requisiciones})

def ordenes_compra(request):
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

    # Puedes agregar más lógica aquí si lo necesitas

    return render(request, 'ordenes_compra.html', {'permisos': permisos, 'user': user})

def logout(request):
    request.session.flush()
    return redirect('index')
