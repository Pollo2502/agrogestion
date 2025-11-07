from compras.models import Requisicion
from usuarios.models import User
from django.contrib import messages
from django.core.mail import send_mail
from telegram_utils import send_telegram_message

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