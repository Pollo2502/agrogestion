from django.shortcuts import render, redirect
from usuarios.models import User
from django.contrib import messages
from .models import SolicitudAnticipo
from django.http import FileResponse, JsonResponse, HttpResponse
import os
import json
from django.template.loader import render_to_string
from io import BytesIO
import zipfile
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone

# Importamos las funciones CRUD de contabilidad
from .crud import generar_portada_pdf_bytes, enviar_zip_original, package_expediente_with_portada

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

    def link_callback(uri, rel):
        """
        Convertir URIs de STATIC/MEDIA a rutas absolutas en disco para xhtml2pdf.
        """
        if uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
            if os.path.exists(path):
                return path
            return uri
        if uri.startswith(settings.STATIC_URL):
            # buscar en staticfiles finders
            rel_path = uri.replace(settings.STATIC_URL, "")
            found = finders.find(rel_path) # type: ignore
            if found:
                return found
            # fallback a STATIC_ROOT
            path = os.path.join(settings.STATIC_ROOT, rel_path)
            if os.path.exists(path):
                return path
            return uri
        # no es static/media: devolver tal cual
        return uri

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

    # Handle form submission for state change, descarga o creación de portada
    if request.method == 'POST':
        accion = request.POST.get('accion')
        solicitud_id = request.POST.get('solicitud_id')

        # Descargar el ZIP original sin portada (trazabilidad marcada en enviar_zip_original)
        if accion == 'descargar_original':
            try:
                solicitud = SolicitudAnticipo.objects.get(id=solicitud_id, contabilidad=user)
                resp = enviar_zip_original(solicitud, user)
                if resp:
                    return resp
                else:
                    messages.error(request, 'No existe un ZIP asociado a esta solicitud.')
                    return redirect('solicitud_anticipo')
            except SolicitudAnticipo.DoesNotExist:
                messages.error(request, 'Solicitud no encontrada.')
                return redirect('solicitud_anticipo')
            except Exception as e:
                messages.error(request, f'Error al descargar el ZIP original: {e}')
                return redirect('solicitud_anticipo')

        # Crear y cargar portada (desde modal checklist)
        if accion == 'crear_portada':
            try:
                solicitud = SolicitudAnticipo.objects.get(id=solicitud_id, contabilidad=user)
                # Si no está marcada la descarga, marcarla ahora con el usuario que crea la portada
                if not (solicitud.zip_descargado and solicitud.zip_descargado_por and solicitud.zip_descargado_por.id == user.id):
                    solicitud.zip_descargado = True
                    solicitud.zip_descargado_por = user
                    solicitud.zip_descargado_fecha = timezone.now()
                    solicitud.save(update_fields=['zip_descargado', 'zip_descargado_por', 'zip_descargado_fecha'])
                    messages.info(request, 'Se registró la descarga del expediente antes de crear la portada.')

                # Generar portada usando la función centralizada
                portada_bytes = generar_portada_pdf_bytes(solicitud, user)
                filename_portada = f"portada_{solicitud.id}.pdf"
                solicitud.portada_pdf.save(filename_portada, ContentFile(portada_bytes), save=True)

                messages.success(request, 'Portada generada y cargada correctamente (firmada).')
            except SolicitudAnticipo.DoesNotExist:
                messages.error(request, 'Solicitud no encontrada.')
            except Exception as e:
                messages.error(request, f'Error al generar la portada: {e}')
            return redirect('solicitud_anticipo')

        # Descargar expediente completo: solo si existe portada
        if accion == 'descargar':
            try:
                solicitud = SolicitudAnticipo.objects.get(id=solicitud_id, contabilidad=user)
                if not solicitud.portada_pdf:
                    messages.error(request, 'No se puede descargar el expediente completo: primero debe crear la portada.')
                    return redirect('solicitud_anticipo')
                # Empaquetar portada + contenido del ZIP original (si existe) y devolver
                resp = package_expediente_with_portada(solicitud, user)
                if resp:
                    return resp
                else:
                    messages.error(request, 'Error al preparar el expediente completo.')
                    return redirect('solicitud_anticipo')
            except SolicitudAnticipo.DoesNotExist:
                messages.error(request, 'Solicitud no encontrada.')
                return redirect('solicitud_anticipo')
            except Exception as e:
                messages.error(request, f'Error al descargar el expediente: {e}')
                return redirect('solicitud_anticipo')

        # Cambios de estado habituales (eliminar si ya no se usan)
        if accion in ('en_proceso', 'finalizar'):
            try:
                solicitud = SolicitudAnticipo.objects.get(id=solicitud_id, contabilidad=user)
                solicitud.estado = 'E' if accion == 'en_proceso' else 'F'
                solicitud.save()
                messages.success(request, f'Solicitud marcada como {"En Proceso" if accion == "en_proceso" else "Finalizada"}.')
            except SolicitudAnticipo.DoesNotExist:
                messages.error(request, 'Solicitud no encontrada.')
            return redirect('solicitud_anticipo')

    # Obtener solicitudes asignadas a este usuario
    solicitudes = SolicitudAnticipo.objects.filter(contabilidad=user)

    context = {
        'user': user,
        'permisos': [],
        'solicitudes': solicitudes,
    }
    return render(request, 'solicitud_anticipo.html', context)


