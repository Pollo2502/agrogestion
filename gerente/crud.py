from compras.models import Requisicion
from usuarios.models import User
from django.contrib import messages
from django.core.mail import send_mail
from telegram_utils import send_telegram_message
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from io import BytesIO
from django.core.files.base import ContentFile

class GerenteAprobacionService:
    @staticmethod
    def firmar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            requisicion = Requisicion.objects.get(id=req_id, gerente=user, estado_preaprobacion='P')
            # Asignar el directivo correspondiente basado en el CECO de la requisición
            directivo = User.objects.filter(puede_aprobar=True).first()
            if not directivo:
                messages.error(request, 'No se encontró un directivo para esta requisición.')
                return

            requisicion.estado_preaprobacion = 'A'  # Cambiar el estado a 'Preaprobada'
            requisicion.directivo = directivo  # Asignar el directivo
            requisicion.save()

            # Firmar PDF con la firma del gerente 2cm por debajo de la firma del requisitor
            try:
                if user.firma and requisicion.archivo and requisicion.archivo.name.lower().endswith('.pdf'):
                    original_pdf = requisicion.archivo.path
                    output_pdf = BytesIO()
                    packet = BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)

                    # Misma configuración de tamaño de firma que en la creación:
                    firma_width = 3 * cm
                    firma_height = 1.5 * cm
                    page_width, page_height = letter

                    # Recalcular posición horizontal para alinear con la firma del requsitor
                    x_directivo = (page_width - firma_width) / 2.5
                    x_requisitor = max(0.5 * cm, x_directivo - firma_width - (0.5 * cm) - (3 * cm))

                    # Bajar 1 cm más la posición base del requisitor (sin salirse de la página)
                    y_requisitor = max(0.1 * cm, (2.7 * cm) - (1 * cm))
                    # Colocar la firma del gerente 2 cm por debajo de la del requisitor
                    y_gerente = max(0.1 * cm, y_requisitor - (2 * cm))

                    # Dibuja la firma del gerente debajo de la del requsitor
                    can.drawImage(user.firma.path, x_requisitor, y_gerente, width=firma_width, height=firma_height, mask='auto')
                    can.save()
                    packet.seek(0)
                    firma_pdf = PdfReader(packet)

                    reader = PdfReader(original_pdf)
                    writer = PdfWriter()
                    for i in range(len(reader.pages)):
                        page = reader.pages[i]
                        if i == len(reader.pages) - 1:
                            page.merge_page(firma_pdf.pages[0])
                        writer.add_page(page)

                    writer.write(output_pdf)
                    output_pdf.seek(0)
                    requisicion.archivo.save(requisicion.archivo.name, ContentFile(output_pdf.read()), save=False)
                    requisicion.save()
            except Exception as e:
                messages.warning(request, f'No fue posible añadir la firma del gerente al PDF: {e}')

            # Enviar notificación por correo al directivo
            if directivo.email:
                subject = f"Requisición {requisicion.codigo} pendiente de su aprobación"
                message = f"""
                Estimado {directivo.nombre},

                La requisición con los siguientes detalles ha sido preaprobada por el gerente {user.nombre} y está pendiente de su aprobación:

                Código: {requisicion.codigo}
                Descripción: {requisicion.descripcion}
                Fecha Requerida: {requisicion.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {requisicion.importancia}

                Por favor, revise la requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',  # Correo del sistema
                    [directivo.email],
                    fail_silently=False,
                )

            # Enviar notificación por correo al requisitor
            if requisicion.usuario.email:
                subject = f"Requisición {requisicion.codigo} preaprobada"
                message = f"""
                Estimado {requisicion.usuario.nombre},

                Su requisición con los siguientes detalles ha sido preaprobada por el gerente {user.nombre}:

                Código: {requisicion.codigo}
                Descripción: {requisicion.descripcion}
                Fecha Requerida: {requisicion.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {requisicion.importancia}

                Por favor, revise el estado de su requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',  # Correo del sistema
                    [requisicion.usuario.email],
                    fail_silently=False,
                )

            # Enviar notificación por Telegram al directivo
            directivo_telegram_message = f"Hola {directivo.nombre}, la requisición {requisicion.codigo} ha sido preaprobada por el gerente {user.nombre} y está pendiente de su aprobación. Por favor, revísela en el sistema."
            send_telegram_message(directivo_telegram_message)

            messages.success(request, f'Requisición {requisicion.codigo} preaprobada y notificada al directivo {directivo.nombre} y al requisitor.')
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada o ya procesada.')

    @staticmethod
    def rechazar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            requisicion = Requisicion.objects.get(id=req_id, gerente=user, estado_preaprobacion='P')
            requisicion.estado_preaprobacion = 'N'  # Cambiar el estado a 'Rechazada'
            requisicion.save()

            # Enviar notificación por correo al directivo
            if requisicion.directivo and requisicion.directivo.email:
                subject = f"Requisición {requisicion.codigo} rechazada"
                message = f"""
                Estimado {requisicion.directivo.nombre},

                La requisición con los siguientes detalles ha sido rechazada por el gerente {user.nombre}:

                Código: {requisicion.codigo}
                Descripción: {requisicion.descripcion}
                Fecha Requerida: {requisicion.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {requisicion.importancia}

                Por favor, revise el estado de la requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',  # Correo del sistema
                    [requisicion.directivo.email],
                    fail_silently=False,
                )

            # Enviar notificación por correo al requisitor
            if requisicion.usuario.email:
                subject = f"Requisición {requisicion.codigo} rechazada"
                message = f"""
                Estimado {requisicion.usuario.nombre},

                Su requisición con los siguientes detalles ha sido rechazada por el gerente {user.nombre}:

                Código: {requisicion.codigo}
                Descripción: {requisicion.descripcion}
                Fecha Requerida: {requisicion.fecha_requerida.strftime('%d/%m/%Y')}
                Importancia: {requisicion.importancia}

                Por favor, revise el estado de su requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',  # Correo del sistema
                    [requisicion.usuario.email],
                    fail_silently=False,
                )

            messages.success(request, f'Requisición {requisicion.codigo} rechazada y notificada al directivo y al requisitor.')
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada o ya procesada.')