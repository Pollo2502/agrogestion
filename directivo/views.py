from django.shortcuts import render, redirect
from .crud import AprobacionService
from usuarios.models import User
from compras.models import Requisicion
from django.contrib import messages
from django.db import transaction
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django.core.files.base import ContentFile

def aprobar_requisiciones(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    permisos = get_permisos(user)

    if request.method == 'POST':
        if 'firmar' in request.POST:
            messages.info(request, 'Entrando a firmar...')
            AprobacionService.firmar_requisicion(request, user)
        elif 'rechazar' in request.POST:
            AprobacionService.rechazar_requisicion(request, user)

    # Solo mostrar requisiciones asignadas a este directivo y pendientes
    requisiciones = Requisicion.objects.filter(directivo=user, estado='P')
    return render(request, 'aprobar.html', {
        'permisos': permisos,
        'user': user,
        'requisiciones': requisiciones,
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
        if req.archivo:
            original_pdf = req.archivo.path
            output_pdf = BytesIO()
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.drawImage(user.firma.path, 400, 50, width=150, height=50, mask='auto')
            can.save()
            packet.seek(0)
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
    except Exception as e:
        messages.error(request, f'Error al firmar: {e}')
        return False
