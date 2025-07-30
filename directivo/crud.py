from compras.models import Requisicion
from django.contrib import messages
from django.db import transaction

class AprobacionService:
    @staticmethod
    @transaction.atomic
    def aprobar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.directivo != user:
                messages.error(request, 'No tienes permiso para aprobar esta requisición')
                return False
            req.estado = 'A'
            req.save()
            messages.success(request, f'Requisición {req.codigo} aprobada exitosamente.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False

    @staticmethod
    @transaction.atomic
    def rechazar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.directivo != user:
                messages.error(request, 'No tienes permiso para rechazar esta requisición')
                return False
            req.estado = 'N'
            req.save()
            messages.success(request, f'Requisición {req.codigo} rechazada.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False