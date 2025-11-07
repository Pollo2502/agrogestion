from .models import OrdenCompra, Requisicion
from django.contrib import messages
from django.db import transaction
from django.core.mail import send_mail
from telegram_utils import send_telegram_message

class OrdenCompraService:
    @staticmethod
    @transaction.atomic
    def crear_orden_compra(request, user):
        try:
            requisicion_id = request.POST.get('requisicion_id')
            archivo_orden = request.FILES.get('archivo_orden')
            archivo_cuadro = request.FILES.get('archivo_cuadro_comparativo')
            archivo_presupuesto = request.FILES.get('archivo_presupuesto')
            archivo_soporte = request.FILES.get('archivo_soporte')
            tipo_soporte = request.POST.get('tipo_soporte')
            observaciones = request.POST.get('observaciones', '')

            requisicion = Requisicion.objects.get(id=requisicion_id, estado='A')
            if hasattr(requisicion, 'orden_compra'):
                messages.error(request, 'Ya existe una orden de compra para esta requisición.')
                return False

            orden = OrdenCompra.objects.create(
                requisicion=requisicion,
                archivo_orden=archivo_orden,
                archivo_cuadro_comparativo=archivo_cuadro,
                archivo_presupuesto=archivo_presupuesto,
                archivo_soporte=archivo_soporte,
                tipo_soporte=tipo_soporte,
                observaciones=observaciones,
                estado='P'
            )
            # Notify via Telegram
            message = f"Se ha creado una nueva orden de compra para la requisición {requisicion_id}."
            send_telegram_message(message)

            # Enviar correo al usuario de compras
            if requisicion.usuario_compras and requisicion.usuario_compras.email:
                subject = f"Requisición {requisicion.id} disponible para compras"
                message = f"""
                Hola {requisicion.usuario_compras.nombre},

                La requisición con los siguientes datos ha sido aprobada y está disponible para compras:

                Código: {requisicion.codigo}
                Descripción: {requisicion.descripcion}
                Fecha de creación: {requisicion.fecha_registro.strftime('%d/%m/%Y')}

                Por favor, revisa la requisición en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    subject,
                    message,
                    'agroluchasistema@gmail.com',  # Correo del sistema
                    [requisicion.usuario_compras.email],
                    fail_silently=False,
                )

            # Enviar notificación al directivo correspondiente
            if requisicion.directivo and requisicion.directivo.email:
                directivo_subject = f"Orden de Compra creada para la Requisición {requisicion.id}"
                directivo_message = f"""
                Hola {requisicion.directivo.nombre},

                Se ha creado una nueva orden de compra para la requisición con los siguientes datos:

                Código: {requisicion.codigo}
                Descripción: {requisicion.descripcion}
                Fecha de creación: {requisicion.fecha_registro.strftime('%d/%m/%Y')}

                Por favor, revisa la orden de compra en el sistema.

                Saludos,
                Equipo de Agrogestión
                """
                send_mail(
                    directivo_subject,
                    directivo_message,
                    'agroluchasistema@gmail.com',  # Correo del sistema
                    [requisicion.directivo.email],
                    fail_silently=False,
                )

                # Enviar mensaje por Telegram al directivo
                directivo_telegram_message = f"Hola {requisicion.directivo.nombre}, se ha creado una nueva orden de compra para la requisición {requisicion.codigo}. Por favor, revisa el sistema."
                send_telegram_message(directivo_telegram_message)

            messages.success(request, 'Orden de compra creada correctamente.')
            return True
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada o no aprobada.')
            return False
        except Exception as e:
            messages.error(request, f'Error al crear orden de compra: {e}')
            return False

    @staticmethod
    @transaction.atomic
    def modificar_orden_compra(request, user, orden_id):
        try:
            orden = OrdenCompra.objects.get(id=orden_id)
            # Solo actualiza los archivos si se suben nuevos
            if request.FILES.get('archivo_orden'):
                orden.archivo_orden = request.FILES.get('archivo_orden')
            if request.FILES.get('archivo_cuadro_comparativo'):
                orden.archivo_cuadro_comparativo = request.FILES.get('archivo_cuadro_comparativo')
            if request.FILES.get('archivo_presupuesto'):
                orden.archivo_presupuesto = request.FILES.get('archivo_presupuesto')
            if request.FILES.get('archivo_soporte'):
                orden.archivo_soporte = request.FILES.get('archivo_soporte')
            # actualizar tipo de soporte si se envía
            tipo_soporte = request.POST.get('tipo_soporte')
            if tipo_soporte is not None:
                orden.tipo_soporte = tipo_soporte
            orden.observaciones = request.POST.get('observaciones', orden.observaciones)
            orden.save()
            messages.success(request, 'Orden de compra modificada correctamente.')
            return True
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden de compra no encontrada.')
            return False

    @staticmethod
    def listar_ordenes():
        return OrdenCompra.objects.all()