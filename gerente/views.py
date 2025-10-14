from django.shortcuts import render, redirect
from .crud import GerenteAprobacionService
from usuarios.models import User
from compras.models import Requisicion
from django.contrib import messages

def panel_gerente(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    # Solo mostrar requisiciones de su CECO pendientes de preaprobación
    requisiciones = Requisicion.objects.filter(gerente=user, estado_preaprobacion='P')

    if request.method == 'POST':
        if 'firmar' in request.POST:
            GerenteAprobacionService.firmar_requisicion(request, user)
            return redirect('panel_gerente')
        elif 'rechazar' in request.POST:
            GerenteAprobacionService.rechazar_requisicion(request, user)
            return redirect('panel_gerente')

    permisos = get_permisos(user)

    # Historial de requisiciones (preaprobadas o rechazadas)
    historial_requisiciones = Requisicion.objects.filter(gerente=user, estado_preaprobacion__in=['A', 'N'])

    return render(request, 'gerente.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones': requisiciones,
        'historial_requisiciones': historial_requisiciones,
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
    if user.es_gerente:
        permisos.append('panel_gerente')
    return permisos
