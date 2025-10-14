from compras.models import Requisicion
from usuarios.models import User
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from io import BytesIO
from django.utils import timezone

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
            usuario_compras_id = request.POST.get('usuario_compras_id')  # Usuario encargado de compras
            directivo_id = request.POST.get('directivo_id')  # Directivo asignado

            if not all([codigo, fecha_requerida, archivo, usuario_compras_id, directivo_id]):
                messages.error(request, 'Todos los campos obligatorios deben ser completados')
                return False

            # Only accept PDF files
            if not archivo.name.lower().endswith('.pdf'):
                messages.error(request, 'El archivo debe ser un PDF')
                return False

            if Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False

            usuario_compras = User.objects.get(id=usuario_compras_id)
            directivo = User.objects.get(id=directivo_id)  # Verifica que el directivo exista

            # Usa el usuario autenticado como creador
            ceco = user.ceco
            gerente = User.objects.filter(ceco=ceco, es_gerente=True).first()
            req = Requisicion(
                codigo=codigo,
                fecha_requerida=fecha_requerida,
                descripcion=descripcion,
                usuario=user,  # Usuario que crea la requisición
                usuario_compras=usuario_compras,  # Usuario encargado de compras
                archivo=archivo,
                importancia=importancia,
                directivo=directivo,  # Asignar el directivo
                ceco=ceco,
                gerente=gerente if gerente else None,
                estado_preaprobacion='P' if gerente else 'A',
            )
            req.save()
            # Firmar el PDF con la firma del requisitor (a la izquierda de la firma del directivo)
            try:
                if user.firma and req.archivo and req.archivo.name.lower().endswith('.pdf'):
                    original_pdf = req.archivo.path
                    output_pdf = BytesIO()
                    packet = BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)

                    # Configuración de la posición y dimensiones de la firma (igual que directivo, pero a la izquierda)
                    firma_width = 3 * cm
                    firma_height = 1.5 * cm
                    page_width, page_height = letter
                    x_directivo = (page_width - firma_width) / 2.5
                    # place requisitor signature to the left of the directivo signature with small gap
                    # move 1 cm further left as requested
                    x_requisitor = max(0.5 * cm, x_directivo - firma_width - (0.5 * cm) - (3 * cm))
                    y = 2.7 * cm

                    # Dibuja la imagen de la firma del requisitor
                    can.drawImage(user.firma.path, x_requisitor, y, width=firma_width, height=firma_height, mask='auto')
                    can.save()
                    packet.seek(0)
                    firma_pdf = PdfReader(packet)

                    # Leer el PDF original y agregar la firma en la última página
                    reader = PdfReader(original_pdf)
                    writer = PdfWriter()
                    for i in range(len(reader.pages)):
                        page = reader.pages[i]
                        if i == len(reader.pages) - 1:
                            page.merge_page(firma_pdf.pages[0])
                        writer.add_page(page)

                    writer.write(output_pdf)
                    output_pdf.seek(0)
                    # Reemplaza el archivo original por la versión firmada
                    req.archivo.save(req.archivo.name, ContentFile(output_pdf.read()), save=False)
                    req.save()
            except Exception as e:
                # No interrumpir la creación si la firma falla, pero notificar
                messages.warning(request, f'No fue posible firmar automáticamente el PDF: {e}')
            messages.success(request, f'Requisición {codigo} creada exitosamente')
            return True

        except User.DoesNotExist:
            messages.error(request, 'El usuario seleccionado no existe')
            return False
        except Exception as e:
            messages.error(request, f'Error al crear requisición: {str(e)}')
            return False

    @staticmethod
    @transaction.atomic
    def editar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)
            if req.usuario != user:
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
            if req.usuario != user:
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