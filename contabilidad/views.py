from django.shortcuts import render, redirect
from usuarios.models import User
from django.contrib import messages
from .models import SolicitudAnticipo
from django.http import FileResponse, JsonResponse
import os
import json

def solicitud_anticipo(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero.')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')

    if not user.puede_contabilidad:
        messages.error(request, 'No tienes permisos para contabilidad.')
        return redirect('login')

    # Handle AJAX request for status update
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            data = json.loads(request.body)
            solicitud_id = data.get('solicitud_id')
            estado = data.get('estado')  # 'F' for Finalizado, 'E' for En Proceso
            solicitud = SolicitudAnticipo.objects.get(id=solicitud_id, contabilidad=user)
            solicitud.estado = estado
            solicitud.save()
            return JsonResponse({'success': True, 'estado': estado})
        except SolicitudAnticipo.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Solicitud no encontrada.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # Handle form submission for state change
    if request.method == 'POST':
        accion = request.POST.get('accion')
        solicitud_id = request.POST.get('solicitud_id')
        try:
            solicitud = SolicitudAnticipo.objects.get(id=solicitud_id, contabilidad=user)
            if accion == 'en_proceso':
                solicitud.estado = 'E'
                solicitud.save()
                messages.success(request, 'Solicitud marcada como En Proceso.')
            elif accion == 'finalizar':
                solicitud.estado = 'F'
                solicitud.save()
                messages.success(request, 'Solicitud marcada como Finalizada.')
        except SolicitudAnticipo.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')

    # Obtener solicitudes asignadas a este usuario
    solicitudes = SolicitudAnticipo.objects.filter(contabilidad=user)

    context = {
        'user': user,
        'permisos': [],
        'solicitudes': solicitudes,
    }
    return render(request, 'solicitud_anticipo.html', context)


