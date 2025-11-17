from compras.models import Requisicion, OrdenCompra
from django.contrib import messages
from django.db import transaction
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

class AprobacionService:
    @staticmethod
    @transaction.atomic
    def aprobar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        if not req_id:
            messages.error(request, 'ID de requisición inválido.')
            return False
        try:
            req_id_int = int(req_id)
        except (ValueError, TypeError):
            messages.error(request, 'ID de requisición inválido.')
            return False
        try:
            req = Requisicion.objects.get(id=req_id_int)
            if req.directivo != user:
                messages.error(request, 'No tienes permiso para aprobar esta requisición')
                return False
            req.estado = 'A'
            req.save()

            # Enviar notificación por correo al creador de la requisición
            if req.usuario.email:
                subject = f"Requisición {req.codigo} aprobada"
                message = f"""
                Estimado {req.usuario.nombre},

                Su requisición con los siguientes detalles ha sido aprobada:

                Código: {req.codigo}
                Descripción: {req.descripcion}
                Fecha Requerida: {req.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {req.importancia}

                Por favor, revise el estado de su requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',
                    [req.usuario.email],
                    fail_silently=False,
                )

            # Enviar notificación por correo al usuario de compras
            if req.usuario_compras and req.usuario_compras.email:
                subject = f"Requisición {req.codigo} aprobada y lista para procesar"
                message = f"""
                Estimado {req.usuario_compras.nombre},

                La requisición con los siguientes detalles ha sido aprobada y está lista para ser procesada:

                Código: {req.codigo}
                Descripción: {req.descripcion}
                Fecha Requerida: {req.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {req.importancia}

                Por favor, revise la requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',
                    [req.usuario_compras.email],
                    fail_silently=False,
                )

            messages.success(request, f'Requisición {req.codigo} aprobada exitosamente.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False

    @staticmethod
    @transaction.atomic
    def rechazar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        if not req_id:
            messages.error(request, 'ID de requisición inválido.')
            return False
        try:
            req_id_int = int(req_id)
        except (ValueError, TypeError):
            messages.error(request, 'ID de requisición inválido.')
            return False
        try:
            req = Requisicion.objects.get(id=req_id_int)
            if req.directivo != user:
                messages.error(request, 'No tienes permiso para rechazar esta requisición')
                return False
            # Guardar comentario de rechazo si fue provisto
            comentario_text = request.POST.get('comentario_rechazo', '').strip()
            if comentario_text:
                from compras.models import RequisicionComentario
                RequisicionComentario.objects.create(
                    requisicion=req,
                    autor=user,
                    mensaje=comentario_text
                )
            req.estado = 'N'
            req.save()

            # Enviar notificación por correo al creador de la requisición
            if req.usuario.email:
                subject = f"Requisición {req.codigo} rechazada"
                message = f"""
                Estimado {req.usuario.nombre},

                Su requisición con los siguientes detalles ha sido rechazada:

                Código: {req.codigo}
                Descripción: {req.descripcion}
                Fecha Requerida: {req.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {req.importancia}

                Comentario del directivo: {comentario_text if comentario_text else 'No se proporcionó un comentario.'}

                Por favor, revise el estado de su requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',
                    [req.usuario.email],
                    fail_silently=False,
                )

            messages.success(request, f'Requisición {req.codigo} rechazada.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False

    @staticmethod
    @transaction.atomic
    def firmar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        if not req_id:
            messages.error(request, 'ID de requisición inválido.')
            return False
        try:
            req_id_int = int(req_id)
        except (ValueError, TypeError):
            messages.error(request, 'ID de requisición inválido.')
            return False
        try:
            req = Requisicion.objects.get(id=req_id_int)
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

                firma_width = 3 * cm
                firma_height = 1.5 * cm
                page_width, page_height = letter
                gap = 3 * cm
                x_directivo_est = (page_width - firma_width) / 2.5
                x_requisitor = max(0.5 * cm, x_directivo_est - firma_width - (0.5 * cm) - (3 * cm))
                x = x_requisitor + firma_width + gap
                y = 2.7 * cm

                # Dibuja la imagen de la firma
                can.drawImage(user.firma.path, x, y, width=firma_width, height=firma_height, mask='auto')

                # Dibuja la fecha, hora y nombre completo del usuario debajo de la firma
                fecha_firma = timezone.now().strftime("%d/%m/%Y %H:%M:%S")
                can.setFont("Helvetica", 10)
                can.drawString(x, y - 15, f"Firmado por: {user.nombre_completo}")
                can.drawString(x, y - 30, f"{fecha_firma}")

                can.save()
                packet.seek(0)
                firma_pdf = PdfReader(packet)

                # Leer el PDF original y agregar la firma en la última página
                reader = PdfReader(original_pdf)
                writer = PdfWriter()
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    if i == len(reader.pages) - 1:  # Agregar la firma solo en la última página
                        page.merge_page(firma_pdf.pages[0])
                    writer.add_page(page)

                # Guardar el PDF firmado
                writer.write(output_pdf)
                output_pdf.seek(0)
                req.archivo_aprobacion.save(
                    f"firmado_{req.archivo.name.split('/')[-1]}",
                    ContentFile(output_pdf.read()),
                    save=False
                )

            req.estado = 'A'
            req.fecha_aprobacion = timezone.now()  # Guarda la fecha de aprobación
            req.save()
            messages.success(request, f'Requisición {req.codigo} firmada y aprobada exitosamente.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al firmar: {e}')
            return False

    @staticmethod
    @transaction.atomic
    def aprobar_orden_compra(request, user):
        orden_id = request.POST.get('orden_id')
        if not orden_id:
            messages.error(request, 'ID de orden inválido.')
            return False
        try:
            orden_id_int = int(orden_id)
        except (ValueError, TypeError):
            messages.error(request, 'ID de orden inválido.')
            return False
        try:
            orden = OrdenCompra.objects.get(id=orden_id_int)
            if not user.firma:
                messages.error(request, 'No tienes firma registrada.')
                return False

            # Firmar el archivo de la orden de compra
            if orden.archivo_orden:
                original_pdf = orden.archivo_orden.path
                output_pdf = BytesIO()
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)

                # Configuración de la posición y dimensiones de la firma
                firma_width = 3 * cm
                firma_height = 1.5 * cm
                page_width, page_height = letter
                # Colocar la firma en la esquina inferior derecha:
                # - 5 cm desde el borde derecho
                # - 3 cm desde la parte inferior
                x = page_width - firma_width - (2 * cm)
                y = 2 * cm

                # Dibuja la imagen de la firma
                can.drawImage(user.firma.path, x, y, width=firma_width, height=firma_height, mask='auto')

                # Dibuja la fecha, hora y nombre completo del usuario debajo de la firma
                fecha_firma = timezone.now().strftime("%d/%m/%Y %H:%M:%S")
                can.setFont("Helvetica", 10)
                can.drawString(x, y - 15, f"Firmado por: {user.nombre_completo}")
                can.drawString(x, y - 30, f"Fecha: {fecha_firma}")

                can.save()
                packet.seek(0)
                firma_pdf = PdfReader(packet)

                # Leer el PDF original y agregar la firma en la primera página
                reader = PdfReader(original_pdf)
                writer = PdfWriter()
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    if i == 0:  # Agregar la firma solo en la primera página
                        page.merge_page(firma_pdf.pages[0])
                    writer.add_page(page)

                # Guardar el PDF firmado
                writer.write(output_pdf)
                output_pdf.seek(0)
                orden.archivo_orden.save(
                    f"firmado_{orden.archivo_orden.name.split('/')[-1]}",
                    ContentFile(output_pdf.read()),
                    save=False
                )

            # Cambiar el estado a aprobada y guardar la fecha de aprobación
            orden.estado = 'A'
            orden.fecha_aprobacion = timezone.now()
            orden.save()

            messages.success(request, f'Orden de compra para la requisición {orden.requisicion.codigo} aprobada y firmada exitosamente.')
            return True
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden de compra no encontrada.')
            return False
        except Exception as e:
            messages.error(request, f'Error al aprobar y firmar la orden de compra: {e}')
            return False

    @staticmethod
    @transaction.atomic
    def rechazar_orden_compra(request, user):
        orden_id = request.POST.get('orden_id')
        comentario_rechazo = request.POST.get('comentario_rechazo', '').strip()
        if not orden_id:
            messages.error(request, 'ID de orden inválido.')
            return False
        try:
            orden_id_int = int(orden_id)
        except (ValueError, TypeError):
            messages.error(request, 'ID de orden inválido.')
            return False
        try:
            orden = OrdenCompra.objects.get(id=orden_id_int)
            orden.estado = 'N'  # Cambiar estado a Rechazada
            orden.observaciones = comentario_rechazo  # Guardar el comentario de rechazo
            orden.save()

            # Guardar el comentario en el modelo OrdenCompraComentario
            from compras.models import OrdenCompraComentario
            OrdenCompraComentario.objects.create(
                orden_compra=orden,
                autor=user,
                mensaje=comentario_rechazo
            )

            # Enviar notificación por correo al usuario de compras
            if orden.requisicion.usuario_compras and orden.requisicion.usuario_compras.email:
                subject = f"Orden de Compra {orden.id} rechazada"
                message = f"""
                Estimado {orden.requisicion.usuario_compras.nombre},

                La orden de compra asociada a la requisición con los siguientes detalles ha sido rechazada:

                Código de Requisición: {orden.requisicion.codigo}
                Descripción: {orden.requisicion.descripcion}
                Fecha de Requerimiento: {orden.requisicion.fecha_requerida.strftime('%d/%m/%Y')}
                Comentario del Directivo: {comentario_rechazo if comentario_rechazo else 'No se proporcionó un comentario.'}

                Por favor, revise el estado de la orden en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',
                    [orden.requisicion.usuario_compras.email],
                    fail_silently=False,
                )

            messages.success(request, f'Orden de compra para la requisición {orden.requisicion.codigo} rechazada.')
            return True
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden de compra no encontrada.')
            return False