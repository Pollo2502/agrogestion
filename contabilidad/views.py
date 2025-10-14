from django.shortcuts import render, redirect
from usuarios.models import User
from django.contrib import messages
from .models import SolicitudAnticipo
from django.shortcuts import redirect
from django.http import FileResponse
import os

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

    # Obtener solicitudes asignadas a este usuario
    solicitudes = SolicitudAnticipo.objects.filter(contabilidad=user)

    # Si se marca una solicitud como en proceso o finalizada
    if request.method == 'POST':
        accion = request.POST.get('accion')
        sol_id = request.POST.get('solicitud_id')
        try:
            sol = SolicitudAnticipo.objects.get(id=sol_id, contabilidad=user)
            if accion == 'en_proceso':
                sol.estado = 'E'
                sol.save()
                messages.success(request, 'Solicitud marcada como en proceso.')
            elif accion == 'finalizar':
                sol.estado = 'F'
                sol.save()
                messages.success(request, 'Solicitud marcada como finalizada.')
            elif accion == 'descargar' and sol.archivo_zip:
                # Devolver el archivo ZIP
                return FileResponse(sol.archivo_zip.open('rb'), as_attachment=True, filename=os.path.basename(sol.archivo_zip.name))
        except SolicitudAnticipo.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')

    context = {
        'user': user,
        'permisos': [],
        'solicitudes': solicitudes,
    }
    return render(request, 'solicitud_anticipo.html', context)


