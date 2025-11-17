from django.shortcuts import render, redirect
from .crud import AprobacionService
from usuarios.models import User
from compras.models import Requisicion, OrdenCompra, RequisicionComentario, OrdenCompraComentario
from django.contrib import messages
from contabilidad.models import SolicitudAnticipo
from django.db import transaction, models  # Import models here
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.core.files.base import ContentFile
import json

def aprobar_requisiciones(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    permisos = get_permisos(user)

    # Verificar permiso de aprobar (directivo)
    if not user.puede_aprobar and not user.es_admin:
        messages.error(request, 'No tienes permisos para aprobar requisiciones.')
        return redirect('login')

    if request.method == 'POST':
        if 'firmar' in request.POST:
            if request.POST.get('req_id'):
                AprobacionService.firmar_requisicion(request, user)
            else:
                messages.error(request, 'No se especificó la requisición para firmar.')
        elif 'rechazar' in request.POST:
            if request.POST.get('req_id'):
                AprobacionService.rechazar_requisicion(request, user)
            else:
                messages.error(request, 'No se especificó la requisición para rechazar.')

    # Filtra las requisiciones pendientes y el historial
    requisiciones_pendientes = Requisicion.objects.filter(
        directivo=user,
        estado_preaprobacion='A',  # Solo las preaprobadas
        estado='P'  # Pendientes
    )
    historial_requisiciones = Requisicion.objects.filter(
        directivo=user
    ).exclude(estado='P')  # Aprobadas o rechazadas

    # Obtener comentarios de rechazo asociados a las requisiciones del directivo
    comentarios_requisiciones = RequisicionComentario.objects.filter(requisicion__directivo=user)
    comentarios_unread_count = comentarios_requisiciones.filter(leido=False).count()

    return render(request, 'aprobar.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones_pendientes': requisiciones_pendientes,
        'historial_requisiciones': historial_requisiciones,
        'comentarios_requisiciones': comentarios_requisiciones,
        'comentarios_unread_count': comentarios_unread_count,
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

def aprobar_compras(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    permisos = get_permisos(user)

    # Verificar permiso de aprobar órdenes
    if not user.puede_aprobar and not user.es_admin:
        messages.error(request, 'No tienes permisos para aprobar órdenes de compra.')
        return redirect('login')

    if request.method == 'POST':
        if 'aprobar' in request.POST:
            AprobacionService.aprobar_orden_compra(request, user)
        elif 'rechazar' in request.POST:
            AprobacionService.rechazar_orden_compra(request, user)

    # Filtra las órdenes de compra pendientes y el historial
    ordenes_pendientes = OrdenCompra.objects.filter(estado='P')  # Pendientes
    historial_ordenes = OrdenCompra.objects.exclude(estado='P')  # Aprobadas o rechazadas

    # Obtener comentarios de rechazo asociados a las órdenes de compra
    from compras.models import OrdenCompraComentario
    comentarios_ordenes = OrdenCompraComentario.objects.filter(
        orden_compra__requisicion__directivo=user
    ).select_related('orden_compra', 'autor')  # Optimizar consultas
    comentarios_unread_count = comentarios_ordenes.filter(leido=False).count()

    return render(request, 'aprobar_compra.html', {
        'permisos': permisos,
        'user': user,
        'ordenes_pendientes': ordenes_pendientes,
        'historial_ordenes': historial_ordenes,
        'comentarios_ordenes': comentarios_ordenes,
        'comentarios_unread_count': comentarios_unread_count,
    })

def panel_directivo(request):
    # Panel estadístico asociado al directivo que está en sesión
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    # permisos para el navbar
    permisos = get_permisos(user)

    # Verificar que el usuario sea directivo/aprobador o admin
    if not user.puede_aprobar and not user.es_admin:
        messages.error(request, 'No tienes permisos para ver este panel.')
        return redirect('login')

    # Requisiciones asociadas al directivo
    requisiciones = Requisicion.objects.filter(directivo=user)

    # Estadísticas resumidas
    total_requisiciones = requisiciones.count()
    pendientes = requisiciones.filter(estado='P').count()
    aprobadas = requisiciones.filter(estado='A').count()
    rechazadas = requisiciones.filter(estado='N').count()

    # Requisiciones con orden de compra
    con_orden = OrdenCompra.objects.filter(requisicion__directivo=user).count()

    # Solicitudes enviadas a contabilidad relacionadas con las ordenes del directivo
    solicitudes = SolicitudAnticipo.objects.filter(orden__requisicion__directivo=user)

    # Buscar tracking por número de requisición
    search_query = request.GET.get('search', '').strip()
    tracking_result = None
    if search_query:
        try:
            solicitud = SolicitudAnticipo.objects.get(orden__requisicion__codigo=search_query)
            tracking_result = solicitud.tracking_text
        except SolicitudAnticipo.DoesNotExist:
            messages.error(request, f'No se encontró una solicitud con el código de requisición: {search_query}')

    # Generate data for the candlestick chart
    requisiciones_volumen = requisiciones.values('fecha_registro').annotate(volumen=models.Count('id')).order_by('fecha_registro')
    candlestick_data = [
        {
            'x': req['fecha_registro'].strftime('%Y-%m-%d'),
            'y': [req['volumen'], req['volumen'], req['volumen'], req['volumen']]
        }
        for req in requisiciones_volumen
    ]

    # Datos para gráficas (pastel)
    count_normal = requisiciones.filter(importancia='N').count()
    count_urgent = requisiciones.filter(importancia='U').count()
    importance_labels = ['Normal', 'Urgente']
    importance_data = [count_normal, count_urgent]

    pre_p = requisiciones.filter(estado_preaprobacion='P').count()
    pre_a = requisiciones.filter(estado_preaprobacion='A').count()
    pre_n = requisiciones.filter(estado_preaprobacion='N').count()
    pre_labels = ['Pendiente', 'Aprobada', 'Negada']
    pre_data = [pre_p, pre_a, pre_n]

    # Construir lista para la tabla "Requisiciones pendientes y responsables"
    # Cada item contiene: codigo, responsables (dict con posibles claves requisitor, compras, gerente, directivo)
    pendientes_qs = requisiciones.filter(estado='P').select_related('usuario', 'usuario_compras', 'gerente', 'directivo')
    esperando_por = []
    for r in pendientes_qs:
        responsables = {
            'requisitor': getattr(r.usuario, 'nombre', None) if getattr(r, 'usuario', None) else None,
            'compras': getattr(r.usuario_compras, 'nombre', None) if getattr(r, 'usuario_compras', None) else None,
            'gerente': getattr(r.gerente, 'nombre', None) if getattr(r, 'gerente', None) else None,
            'directivo': getattr(r.directivo, 'nombre', None) if getattr(r, 'directivo', None) else None,
        }
        esperando_por.append({
            'codigo': r.codigo,
            'responsables': responsables,
            'estado_preaprobacion': r.estado_preaprobacion,
        })

    # Debugging: Print data for pie charts
    print("Importance Data:", importance_data)
    print("Pre-Approval Data:", pre_data)

    context = {
        'user': user,
        'permisos': permisos,
        'total_requisiciones': total_requisiciones,
        'pendientes': pendientes,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
        'con_orden': con_orden,
        'solicitudes': solicitudes,
        'esperando_por': esperando_por,
        'tracking_result': tracking_result,
        'search_query': search_query,
        'candlestick_data_json': json.dumps(candlestick_data),
        'importance_labels_json': json.dumps(importance_labels),
        'importance_data_json': json.dumps(importance_data),
        'pre_labels_json': json.dumps(pre_labels),
        'pre_data_json': json.dumps(pre_data),
    }

    return render(request, 'panel_estadistico.html', context)
