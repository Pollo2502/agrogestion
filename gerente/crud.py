from compras.models import Requisicion
from django.contrib import messages
from django.db import transaction
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

class GerenteAprobacionService:
    @staticmethod
    @transaction.atomic
    def firmar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.gerente != user:
                messages.error(request, 'No tienes permiso para aprobar esta requisición')
                return False
            # Solo cambia el estado de preaprobación, NO firma el PDF
            req.estado_preaprobacion = 'A'
            req.save()
            messages.success(request, f'Requisición {req.codigo} preaprobada exitosamente.')
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
            if req.gerente != user:
                messages.error(request, 'No tienes permiso para rechazar esta requisición')
                return False
            req.estado_preaprobacion = 'N'
            req.save()
            messages.success(request, f'Requisición {req.codigo} rechazada.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False