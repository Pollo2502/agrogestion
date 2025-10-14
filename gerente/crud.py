from compras.models import Requisicion
from usuarios.models import User
from django.contrib import messages

class GerenteAprobacionService:
    @staticmethod
    def firmar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            requisicion = Requisicion.objects.get(id=req_id, gerente=user, estado_preaprobacion='P')
            # Asignar el directivo correspondiente basado en el CECO de la requisición
            directivo = User.objects.filter(puede_aprobar=True,).first()
            if not directivo:
                messages.error(request, 'No se encontró un directivo para esta requisición.')
                return

            requisicion.estado_preaprobacion = 'A'  # Cambiar el estado a 'Preaprobada'
            requisicion.directivo = directivo  # Asignar el directivo
            requisicion.save()
            messages.success(request, f'Requisición {requisicion.codigo} preaprobada y asignada al directivo {directivo.nombre}.')
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada o ya procesada.')

    @staticmethod
    def rechazar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            requisicion = Requisicion.objects.get(id=req_id, gerente=user, estado_preaprobacion='P')
            requisicion.estado_preaprobacion = 'N'  # Cambiar el estado a 'Rechazada'
            requisicion.save()
            messages.success(request, f'Requisición {requisicion.codigo} rechazada exitosamente.')
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada o ya procesada.')