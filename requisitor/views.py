from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from usuarios.models import User
from compras.models import Requisicion
from .crud import RequisicionService


def crear_requisiciones(request):
    user_id = request.session.get('user_id')
    if not user_id:
        # Redirige a login o muestra error
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    permisos = get_permisos(user)

    compradores = User.objects.filter(puede_compras=True)
    directivos = User.objects.filter(puede_aprobar=True)  # <-- agrega esto

    # CRUD actions
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            RequisicionService.crear_requisicion(request, user)
        elif accion == 'editar':
            RequisicionService.editar_requisicion(request, user)
        # Puedes agregar aquí eliminar si lo necesitas

    requisiciones = Requisicion.objects.all()
    return render(request, 'crear_requisiciones.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones': requisiciones,
        'compradores': compradores,
        'directivos': directivos,  # <-- pásalo al template
    })

def logout(request):
    request.session.flush()
    return redirect('index')

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

def tu_vista(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    usuario = user  # El usuario autenticado pasado desde la vista
    ceco = usuario.ceco
    gerente = User.objects.filter(ceco=ceco, es_gerente=True).first()