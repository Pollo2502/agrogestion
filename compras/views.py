from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usuarios.models import User  # Importa el modelo User desde la app usuarios
from django.core.files.base import ContentFile
from contabilidad.models import SolicitudAnticipo
from .models import Requisicion
from .crud import OrdenCompraService
from .models import OrdenCompra
import zipfile
from io import BytesIO
from django.http import HttpResponse
from django.utils.timezone import now
from django.utils import timezone


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
    if user.puede_aprobar:
        permisos.append('aprobar_requisiciones')
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

    # Verificar permiso de compras
    if not user.puede_compras and not user.es_admin:
        messages.error(request, 'No tienes permisos para acceder a Compras.')
        return redirect('login')

    # Filtrar requisiciones según el rol del usuario
    if user.puede_compras and not user.es_admin:
        # Mostrar solo las requisiciones asignadas al comprador
        requisiciones = Requisicion.objects.filter(usuario_compras=user, estado='A')
    elif user.es_admin:
        # Mostrar todas las requisiciones para administradores
        requisiciones = Requisicion.objects.all()
    else:
        # Mostrar requisiciones creadas por el usuario
        requisiciones = Requisicion.objects.filter(usuario=user)

    return render(request, 'requisiciones.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones': requisiciones,
    })

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

    # Filtrar requisiciones aprobadas según el rol del usuario
    if user.puede_compras and not user.es_admin:
        # Mostrar solo las requisiciones asignadas al comprador
        requisiciones_aprobadas = Requisicion.objects.filter(usuario_compras=user, estado='A').exclude(orden_compra__isnull=False)
    elif user.es_admin:
        # Mostrar todas las requisiciones aprobadas sin orden de compra
        requisiciones_aprobadas = Requisicion.objects.filter(estado='A').exclude(orden_compra__isnull=False)
    else:
        # Si el usuario no tiene permisos de compras, no mostrar requisiciones
        requisiciones_aprobadas = Requisicion.objects.none()

    # Mostrar todas las órdenes de compra
    ordenes = OrdenCompra.objects.all()

    if request.method == 'POST':
        OrdenCompraService.crear_orden_compra(request, user)
        return redirect('ordenes_compra')

    # pasar lista de usuarios de contabilidad para asignar expediente
    contabilidad_users = User.objects.filter(puede_contabilidad=True)

    # Obtener comentarios de rechazo asociados a las órdenes de compra del usuario
    from .models import OrdenCompraComentario
    comentarios_ordenes = OrdenCompraComentario.objects.filter(
        orden_compra__requisicion__usuario_compras=user
    ).select_related('orden_compra', 'autor')  # Optimizar consultas
    comentarios_unread_count = comentarios_ordenes.filter(leido=False).count()

    return render(request, 'ordenes_compra.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones_aprobadas': requisiciones_aprobadas,
        'ordenes': ordenes,
        'contabilidad_users': contabilidad_users,
        'comentarios_ordenes': comentarios_ordenes,
        'comentarios_unread_count': comentarios_unread_count,
    })


def enviar_expediente_a_contabilidad(request):
    if request.method != 'POST':
        return redirect('ordenes_compra')

    orden_id = request.POST.get('orden_id')
    contabilidad_id = request.POST.get('contabilidad_id')
    try:
        orden = OrdenCompra.objects.get(id=orden_id)
    except OrdenCompra.DoesNotExist:
        messages.error(request, 'Orden de compra no encontrada.')
        return redirect('ordenes_compra')

    # Verificar permiso de compras
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = None
    if not user or (not user.puede_compras and not user.es_admin):
        messages.error(request, 'No tienes permisos para enviar expedientes.')
        return redirect('ordenes_compra')

    try:
        cont_user = User.objects.get(id=contabilidad_id) if contabilidad_id else None
    except User.DoesNotExist:
        cont_user = None

    # Solo enviar si la orden está aprobada
    if orden.estado != 'A':
        messages.error(request, 'La orden debe estar aprobada para enviar el expediente.')
        return redirect('ordenes_compra')

    # Crear tracking y ZIP en memoria
    tracking_content = f"""
    Expediente de Orden de Compra
    =============================
    Código de Requisición: {orden.requisicion.codigo}
    Usuario que creó la requisición: {orden.requisicion.usuario.nombre}
    Fecha de creación de la requisición: {orden.requisicion.fecha_registro.strftime('%d/%m/%Y')}
    Estado de preaprobacion: {orden.requisicion.get_estado_preaprobacion_display()}
    Directivo que aprobó: {orden.requisicion.directivo.nombre if orden.requisicion.directivo else 'N/A'}
    Fecha de aprobación: {orden.requisicion.fecha_aprobacion.strftime('%d/%m/%Y') if orden.requisicion.fecha_aprobacion else 'N/A'}
    Tipo soporte: {orden.get_tipo_soporte_display() if orden.tipo_soporte else 'N/A'}
    =============================
    Archivos relacionados:
    - Orden de Compra
    - Cuadro Comparativo
    - Presupuesto
    - Requisición
    - Documento de soporte ({orden.get_tipo_soporte_display() if orden.tipo_soporte else 'Sin tipo'})
    """

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('tracking.txt', tracking_content)
        if orden.archivo_orden:
            zip_file.write(orden.archivo_orden.path, f'OrdenCompra_{orden.requisicion.codigo}.pdf')
        if orden.archivo_cuadro_comparativo:
            zip_file.write(orden.archivo_cuadro_comparativo.path, f'CuadroComparativo_{orden.requisicion.codigo}.pdf')
        if orden.archivo_presupuesto:
            zip_file.write(orden.archivo_presupuesto.path, f'Presupuesto_{orden.requisicion.codigo}.pdf')
        if orden.requisicion.archivo:
            zip_file.write(orden.requisicion.archivo.path, f'Requisicion_{orden.requisicion.codigo}.pdf')
        if orden.archivo_soporte:
            ext_name = orden.archivo_soporte.name.split('/')[-1]
            zip_file.write(orden.archivo_soporte.path, f'Soporte_{orden.requisicion.codigo}_{ext_name}')

    zip_buffer.seek(0)

    # Guardar la solicitud y asignar al usuario de contabilidad
    solicitud, created = SolicitudAnticipo.objects.get_or_create(orden=orden)
    solicitud.contabilidad = cont_user
    solicitud.tracking_text = tracking_content
    solicitud.fecha_envio = timezone.now()  # Set the fecha_envio explicitly
    # Guardar el archivo ZIP en el campo archivo_zip
    solicitud.archivo_zip.save(f'Expediente_{orden.requisicion.codigo}.zip', ContentFile(zip_buffer.read()), save=False)
    solicitud.save()

    messages.success(request, 'Expediente enviado a contabilidad correctamente.')
    return redirect('ordenes_compra')

def logout(request):
    request.session.flush()
    return redirect('index')

def mandar_expediente(request, orden_id):
    try:
        # Obtener la orden de compra
        orden = OrdenCompra.objects.get(id=orden_id)

        # Verificar si la orden de compra está aprobada
        if orden.estado != 'A':  # Suponiendo que 'A' significa "Aprobada"
            messages.error(request, 'No puedes mandar el expediente porque la orden de compra no está aprobada.')
            return redirect('ordenes_compra')

        # Crear el archivo de tracking
        tracking_content = f"""
        Expediente de Orden de Compra
        =============================
        Código de Requisición: {orden.requisicion.codigo}
        Usuario que creó la requisición: {orden.requisicion.usuario.nombre}
        Fecha de creación de la requisición: {orden.requisicion.fecha_registro.strftime('%d/%m/%Y')}
        Estado de preaprobación: {orden.requisicion.get_estado_preaprobacion_display()}
        Directivo que aprobó: {orden.requisicion.directivo.nombre if orden.requisicion.directivo else 'N/A'}
        Fecha de aprobación: {orden.requisicion.fecha_aprobacion.strftime('%d/%m/%Y') if orden.requisicion.fecha_aprobacion else 'N/A'}
        Tipo soporte: {orden.get_tipo_soporte_display() if orden.tipo_soporte else 'N/A'}
        =============================
        Archivos relacionados:
        - Orden de Compra
        - Cuadro Comparativo
        - Presupuesto
        - Requisición
        - Documento de soporte ({orden.get_tipo_soporte_display() if orden.tipo_soporte else 'Sin tipo'})
        """

        # Crear un archivo ZIP en memoria
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Agregar el archivo de tracking
            zip_file.writestr('tracking.txt', tracking_content)

            # Agregar los archivos relacionados
            if orden.archivo_orden:
                zip_file.write(orden.archivo_orden.path, f'OrdenCompra_{orden.requisicion.codigo}.pdf')
            if orden.archivo_cuadro_comparativo:
                zip_file.write(orden.archivo_cuadro_comparativo.path, f'CuadroComparativo_{orden.requisicion.codigo}.pdf')
            if orden.archivo_presupuesto:
                zip_file.write(orden.archivo_presupuesto.path, f'Presupuesto_{orden.requisicion.codigo}.pdf')
            if orden.requisicion.archivo:
                zip_file.write(orden.requisicion.archivo.path, f'Requisicion_{orden.requisicion.codigo}.pdf')
            if orden.archivo_soporte:
                ext_name = orden.archivo_soporte.name.split('/')[-1]
                zip_file.write(orden.archivo_soporte.path, f'Soporte_{orden.requisicion.codigo}_{ext_name}')

        # Verificar permisos del usuario que realiza la acción
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'Debe iniciar sesión primero.')
            return redirect('login')
        try:
            actor = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
            return redirect('login')
        if not actor.puede_compras and not actor.es_admin:
            messages.error(request, 'No tienes permisos para mandar el expediente.')
            return redirect('ordenes_compra')

        # Preparar la respuesta HTTP con el archivo ZIP
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename=Expediente_{orden.requisicion.codigo}_{now().strftime("%Y%m%d")}.zip'
        return response

    except OrdenCompra.DoesNotExist:
        messages.error(request, 'Orden de compra no encontrada.')
        return redirect('ordenes_compra')
    except Exception as e:
        messages.error(request, f'Error al generar el expediente: {e}')
        return redirect('ordenes_compra')

def cargar_soporte(request):
    if request.method != 'POST':
        return redirect('ordenes_compra')

    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero.')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')

    # Verificar permiso de compras
    if not user.puede_compras and not user.es_admin:
        messages.error(request, 'No tienes permisos para cargar soportes.')
        return redirect('ordenes_compra')

    orden_id = request.POST.get('orden_id')
    if not orden_id:
        messages.error(request, 'Orden no especificada.')
        return redirect('ordenes_compra')

    try:
        # Reutiliza la función de modificación que actualiza archivo_soporte y tipo_soporte
        success = OrdenCompraService.modificar_orden_compra(request, user, orden_id)
        if success:
            messages.success(request, 'Documento de soporte guardado correctamente.')
        else:
            # modificar_orden_compra ya pone mensajes, solo redirigir
            pass
    except Exception as e:
        messages.error(request, f'Error al guardar documento de soporte: {e}')

    return redirect('ordenes_compra')

def editar_orden_compra(request):
    if request.method == 'POST':
        orden_id = request.POST.get('orden_id')
        orden = get_object_or_404(OrdenCompra, id=orden_id)

        # Actualizar archivos si se suben nuevos
        if 'archivo_orden' in request.FILES:
            orden.archivo_orden = request.FILES['archivo_orden']
        if 'archivo_cuadro_comparativo' in request.FILES:
            orden.archivo_cuadro_comparativo = request.FILES['archivo_cuadro_comparativo']
        if 'archivo_presupuesto' in request.FILES:
            orden.archivo_presupuesto = request.FILES['archivo_presupuesto']

        # Actualizar observaciones
        orden.observaciones = request.POST.get('observaciones', orden.observaciones)

        # Cambiar el estado a pendiente
        orden.estado = 'P'
        orden.save()

        messages.success(request, 'Orden de compra actualizada y marcada como pendiente.')
        return redirect('ordenes_compra')
    return redirect('ordenes_compra')