from compras.models import Requisicion
from django.contrib import messages
from django.db import transaction
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.conf import settings

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

    @staticmethod
    @transaction.atomic
    def firmar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.directivo != user:
                messages.error(request, 'No tienes permiso para firmar esta requisición')
                return False
            if not user.firma:
                messages.error(request, 'No tienes firma registrada')
                return False
            # Insertar firma en el PDF y guardar en archivo_aprobacion
            if req.archivo:
                original_pdf = req.archivo.path
                output_pdf = BytesIO()
                # Crear un PDF con la firma usando reportlab
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.drawImage(user.firma.path, 400, 50, width=150, height=50, mask='auto')
                can.save()
                packet.seek(0)
                # Mezclar la firma con la primera página del PDF
                reader = PdfReader(original_pdf)
                writer = PdfWriter()
                signature_pdf = PdfReader(packet)
                page = reader.pages[0]
                page.merge_page(signature_pdf.pages[0])
                writer.add_page(page)
                for i in range(1, len(reader.pages)):
                    writer.add_page(reader.pages[i])
                writer.write(output_pdf)
                output_pdf.seek(0)
                # Guardar el nuevo PDF en el campo archivo_aprobacion
                req.archivo_aprobacion.save(
                    f"firmado_{req.archivo.name.split('/')[-1]}",
                    ContentFile(output_pdf.read()),
                    save=False
                )
            req.estado = 'A'
            req.save()
            messages.success(request, f'Requisición {req.codigo} firmada y aprobada exitosamente.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False