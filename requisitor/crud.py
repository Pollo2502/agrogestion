from compras.models import Requisicion
from usuarios.models import User
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.core.files.storage import default_storage

class RequisicionService:
    @staticmethod
    @transaction.atomic
    def crear_requisicion(request, user):
        try:
            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida')
            descripcion = request.POST.get('descripcion', '').strip()
            archivo = request.FILES.get('archivo')
            importancia = request.POST.get('importancia', 'N')
            usuario_com_id = request.POST.get('usuario_com_id')  # <-- nuevo
            directivo_id = request.POST.get('directivo_id')  # <-- nuevo

            if not all([codigo, fecha_requerida, archivo, usuario_com_id, directivo_id]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados')
                return False

            if Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False

            usuario_com = User.objects.get(id=usuario_com_id)
            directivo = User.objects.get(id=directivo_id)

            req = Requisicion(
                codigo=codigo,
                fecha_requerida=fecha_requerida,
                descripcion=descripcion,
                usuario=usuario_com,  # <-- asignar comprador
                creador_req=user.nombre,
                archivo=archivo,
                importancia=importancia,
                directivo=directivo,  # <-- asignar directivo
            )
            req.save()
            messages.success(request, f'Requisición {codigo} creada exitosamente')
            return True

        except Exception as e:
            messages.error(request, f'Error al crear requisición: {str(e)}')
            return False

    @staticmethod
    @transaction.atomic
    def editar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.creador_req != user.nombre:
                messages.error(request, 'No tienes permiso para editar esta requisición')
                return False

            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida')
            descripcion = request.POST.get('descripcion', '').strip()
            importancia = request.POST.get('importancia', 'N')

            if not codigo:
                messages.error(request, 'El código es obligatorio')
                return False

            if codigo != req.codigo and Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False

            if 'archivo' in request.FILES:
                archivo = request.FILES['archivo']
                if archivo.name.lower().endswith('.pdf') and archivo.size <= 5 * 1024 * 1024:
                    if req.archivo:
                        req.archivo.delete()
                    req.archivo = archivo
                else:
                    messages.error(request, 'El archivo debe ser PDF y menor a 5MB')

            if 'archivo_aprobacion' in request.FILES:
                archivo_aprobacion = request.FILES['archivo_aprobacion']
                if archivo_aprobacion.name.lower().endswith('.pdf') and archivo_aprobacion.size <= 5 * 1024 * 1024:
                    if req.archivo_aprobacion:
                        req.archivo_aprobacion.delete()
                    req.archivo_aprobacion = archivo_aprobacion
                    req.estado = 'A'
                else:
                    messages.error(request, 'El archivo de aprobación debe ser PDF y menor a 5MB')

            req.codigo = codigo
            req.fecha_requerida = fecha_requerida
            req.descripcion = descripcion
            req.importancia = importancia
            req.save()
            messages.success(request, f'Requisición {codigo} actualizada exitosamente!')
            return True

        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al actualizar requisición: {str(e)}')
            return False

    @staticmethod
    @transaction.atomic
    def eliminar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.creador_req != user.nombre:
                messages.error(request, 'No tienes permiso para eliminar esta requisición')
                return False

            codigo = req.codigo
            if req.archivo:
                try:
                    default_storage.delete(req.archivo.path)
                except Exception as e:
                    messages.error(request, f'Error al eliminar el archivo: {str(e)}')
                    return False

            req.delete()
            messages.success(request, f'Requisición {codigo} eliminada exitosamente!')
            return True

        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al eliminar requisición: {str(e)}')
            return False