from django.template.loader import render_to_string
from django.conf import settings
from django.http import FileResponse
from io import BytesIO
import os
import zipfile
from django.utils import timezone
from weasyprint import HTML as WeasyHTML
from django.contrib.staticfiles import finders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import base64
import mimetypes

def link_callback(uri, rel):
    # Convierte URIs STATIC/MEDIA a rutas físicas para xhtml2pdf / wkhtmltopdf
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        if os.path.exists(path):
            return path
        return uri
    if uri.startswith(settings.STATIC_URL):
        rel_path = uri.replace(settings.STATIC_URL, "")
        found = finders.find(rel_path)
        if found:
            return found
        path = os.path.join(settings.STATIC_ROOT or '', rel_path)
        if os.path.exists(path):
            return path
        return uri
    return uri

def generar_portada_pdf_bytes(solicitud, contabilidad_user):
    """
    Renderiza la plantilla portada_expediente.html usando WeasyPrint exclusivamente.
    Devuelve bytes del PDF. Si WeasyPrint no está instalado, lanza RuntimeError indicando cómo instalarlo.
    """
    if not WeasyHTML:
        raise RuntimeError(
            "WeasyPrint no está disponible. Instálalo con: "
            "pip install weasyprint (y las dependencias del sistema: cairo, pango, gdk-pixbuf)."
        )

    context = {
        'solicitud': solicitud,
        'orden': solicitud.orden,
        'requisicion': solicitud.orden.requisicion,
        'user': contabilidad_user,
        'now': timezone.now(),
    }
    html = render_to_string('portada_expediente.html', context)
    # Si el usuario de contabilidad tiene firma, embebe la imagen en el HTML como data URI
    try:
        if getattr(contabilidad_user, 'firma', None):
            # Intentar obtener ruta del archivo y leer bytes
            try:
                firma_path = contabilidad_user.firma.path
            except Exception:
                # fallback: intentar construir desde MEDIA_ROOT+url
                firma_url = getattr(contabilidad_user.firma, 'url', None)
                firma_path = None
                if firma_url and firma_url.startswith(settings.MEDIA_URL):
                    firma_path = os.path.join(settings.MEDIA_ROOT, firma_url.replace(settings.MEDIA_URL, '').lstrip('/'))
            if firma_path and os.path.exists(firma_path):
                with open(firma_path, 'rb') as f:
                    img_bytes = f.read()
                mime, _ = mimetypes.guess_type(firma_path)
                if not mime:
                    mime = 'image/png'
                data_uri = 'data:%s;base64,%s' % (mime, base64.b64encode(img_bytes).decode('ascii'))
                # Reemplazar la URL de la firma (rendered) por data URI en el HTML
                firma_url_rendered = getattr(contabilidad_user.firma, 'url', None)
                if firma_url_rendered and firma_url_rendered in html:
                    html = html.replace(firma_url_rendered, data_uri)
                else:
                    # En algunos entornos la plantilla podría renderizar rutas relativas; reemplazar filename si corresponde
                    fname = os.path.basename(firma_path)
                    if fname and fname in html:
                        html = html.replace(fname, data_uri)
    except Exception:
        # No bloquear la generación por problemas al leer la firma; WeasyPrint podrá fallar después con mensaje claro.
        pass

    # Determinar base_url para resolver recursos estáticos/media
    base_url = None
    if getattr(settings, 'STATIC_ROOT', None):
        base_url = settings.STATIC_ROOT
    elif getattr(settings, 'STATICFILES_DIRS', None):
        try:
            base_url = settings.STATICFILES_DIRS[0]
        except Exception:
            base_url = None
    if not base_url and getattr(settings, 'MEDIA_ROOT', None):
        base_url = settings.MEDIA_ROOT
    if not base_url:
        base_url = os.path.abspath(os.getcwd())

    # Generar PDF con WeasyPrint
    try:
        pdf_bytes = WeasyHTML(string=html, base_url=base_url).write_pdf()
        return pdf_bytes
    except Exception as e:
        # Si falla WeasyPrint por cualquier motivo, lanzar error detallado
        raise RuntimeError(f'Error al generar PDF con WeasyPrint: {e}')

def enviar_zip_original(solicitud, usuario):
    """
    Devuelve FileResponse del ZIP original (sin portada). Marca trazabilidad en el modelo.
    Retorna None si no existe archivo_zip.
    """
    if not solicitud.archivo_zip:
        return None
    try:
        zip_path = solicitud.archivo_zip.path
        f = open(zip_path, 'rb')
        response = FileResponse(f, as_attachment=True, filename=os.path.basename(zip_path))
    except Exception:
        solicitud.archivo_zip.open('rb')
        solicitud.archivo_zip.seek(0)
        response = FileResponse(solicitud.archivo_zip, as_attachment=True, filename=os.path.basename(solicitud.archivo_zip.name))
    solicitud.zip_descargado = True
    solicitud.zip_descargado_por = usuario
    solicitud.zip_descargado_fecha = timezone.now()
    solicitud.save(update_fields=['zip_descargado', 'zip_descargado_por', 'zip_descargado_fecha'])
    return response

def package_expediente_with_portada(solicitud, usuario):
    """
    Empaqueta portada.pdf (desde solicitud.portada_pdf) como primer archivo y luego
    añade los archivos del ZIP original (si existe). Marca trazabilidad y devuelve FileResponse.
    """
    if not solicitud.portada_pdf:
        return None
    # leer portada bytes
    try:
        portada_path = solicitud.portada_pdf.path
        with open(portada_path, 'rb') as f:
            portada_bytes = f.read()
    except Exception:
        solicitud.portada_pdf.open('rb')
        solicitud.portada_pdf.seek(0)
        portada_bytes = solicitud.portada_pdf.read()
    # Crear zip en memoria
    out_io = BytesIO()
    with zipfile.ZipFile(out_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr('portada.pdf', portada_bytes)
        if solicitud.archivo_zip:
            try:
                existing_path = solicitud.archivo_zip.path
                with zipfile.ZipFile(existing_path, mode='r') as zin:
                    for item in zin.infolist():
                        data = zin.read(item.filename)
                        zout.writestr(item.filename, data)
            except Exception:
                try:
                    solicitud.archivo_zip.open('rb')
                    solicitud.archivo_zip.seek(0)
                    with zipfile.ZipFile(solicitud.archivo_zip, mode='r') as zin:
                        for item in zin.infolist():
                            data = zin.read(item.filename)
                            zout.writestr(item.filename, data)
                except Exception:
                    pass
    out_io.seek(0)
    solicitud.zip_descargado = True
    solicitud.zip_descargado_por = usuario
    solicitud.zip_descargado_fecha = timezone.now()
    solicitud.save(update_fields=['zip_descargado', 'zip_descargado_por', 'zip_descargado_fecha'])
    filename = f"{solicitud.orden.requisicion.codigo}_expediente_completo.zip"
    return FileResponse(out_io, as_attachment=True, filename=filename)
