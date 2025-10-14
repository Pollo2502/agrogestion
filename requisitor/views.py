from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from usuarios.models import User
from compras.models import Requisicion
from .crud import RequisicionService


def crear_requisiciones(request):
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

    # Verificar permiso de crear requisiciones
    if not user.puede_requisiciones and not user.es_admin:
        messages.error(request, 'No tienes permisos para crear requisiciones.')
        return redirect('login')

    compradores = User.objects.filter(puede_compras=True)
    directivos = User.objects.filter(puede_aprobar=True)

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            RequisicionService.crear_requisicion(request, user)
        elif accion == 'editar':
            RequisicionService.editar_requisicion(request, user)
        return redirect('crear_requisiciones')

    # Filtrar requisiciones solo del usuario autenticado
    requisiciones = Requisicion.objects.filter(usuario=user)

    # Comentarios de rechazo asociados a las requisiciones del usuario
    from compras.models import RequisicionComentario
    comentarios_requisitor = RequisicionComentario.objects.filter(requisicion__usuario=user)
    comentarios_unread_count = RequisicionComentario.objects.filter(requisicion__usuario=user, leido=False).count()

    return render(request, 'crear_requisiciones.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones': requisiciones,
        'compradores': compradores,
        'directivos': directivos,
        'comentarios_requisitor': comentarios_requisitor,
        'comentarios_unread_count': comentarios_unread_count,
    })

def logout(request):
    request.session.flush()
    return redirect('login')


def marcar_comentarios_leidos(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    from compras.models import RequisicionComentario
    RequisicionComentario.objects.filter(requisicion__usuario=user, leido=False).update(leido=True)
    return redirect('crear_requisiciones')

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
