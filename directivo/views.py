from django.shortcuts import render, redirect
from .crud import AprobacionService
from usuarios.models import User
from compras.models import Requisicion

def aprobar_requisiciones(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    permisos = get_permisos(user)

    if request.method == 'POST':
        if 'aprobar' in request.POST:
            AprobacionService.aprobar_requisicion(request, user)
        elif 'rechazar' in request.POST:
            AprobacionService.rechazar_requisicion(request, user)

    # Solo mostrar requisiciones asignadas a este directivo y pendientes
    requisiciones = Requisicion.objects.filter(directivo=user, estado='P')
    return render(request, 'aprobar.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones': requisiciones,
    })


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
