import os
import secrets
from PIL import Image
from flask import current_app, url_for, abort
from werkzeug.datastructures import FileStorage
import qrcode
from flask_mail import Message
from app.extensions import mail
from functools import wraps
from flask_login import current_user
import logging
import re
import unicodedata

# Configuración de Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('logs/utils.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# Decorador para requerir permisos de administrador
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning("Acceso denegado. Usuario no es administrador.")
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

# Función para normalizar nombres
def normalize_name(name):
    """Normaliza el nombre eliminando acentos, convirtiendo a minúsculas,
    eliminando caracteres especiales y reemplazando espacios múltiples por uno solo."""
    name = name.strip()
    name = " ".join(name.split())  # Elimina espacios adicionales entre palabras
    name_normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()
    name_normalized = re.sub(r'[^a-z0-9]+', ' ', name_normalized).strip()
    return name_normalized

# Función para guardar la imagen de perfil
def save_profile_picture(form_picture, folder='profile_pics', output_size=(300, 300), quality=90):
    """
    Guarda una foto de perfil redimensionada con buena calidad.
    
    :param form_picture: El archivo de imagen subido.
    :param folder: El directorio donde se guardará la imagen.
    :param output_size: El tamaño máximo de la imagen redimensionada.
    :param quality: El nivel de calidad de la imagen guardada (0-100), donde 100 es la mejor calidad.
    """
    if not isinstance(form_picture, FileStorage):
        logger.error("El objeto proporcionado no es un archivo válido")
        raise ValueError("El objeto proporcionado no es un archivo válido")

    # Verificar si el directorio existe o crearlo
    picture_dir = os.path.join(current_app.root_path, 'static', folder)
    os.makedirs(picture_dir, exist_ok=True)

    # Generar un nombre único para el archivo de la imagen
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(picture_dir, picture_fn)

    try:
        # Abrir y redimensionar la imagen manteniendo la relación de aspecto
        i = Image.open(form_picture)
        i.thumbnail(output_size, Image.LANCZOS)  # Redimensionar con alta calidad de filtro

        # Guardar la imagen con la calidad definida y optimización
        i.save(picture_path, quality=quality, optimize=True)
        logger.info(f"Foto de perfil guardada en: {picture_path}")

    except Exception as e:
        logger.error(f"Error al guardar la foto de perfil: {e}")
        raise

    return picture_fn

# Función para guardar la imagen de un contenedor
def save_container_picture(form_picture, folder='container_pics', output_size=(800, 800), quality=85):
    """Guarda una imagen del contenedor redimensionada."""
    if not isinstance(form_picture, FileStorage):
        logger.error("El objeto proporcionado no es un archivo válido")
        raise ValueError("El objeto proporcionado no es un archivo válido")

    # Verificar que el directorio existe
    picture_dir = os.path.join(current_app.root_path, 'static', folder)
    os.makedirs(picture_dir, exist_ok=True)

    # Crear un nombre de archivo único y redimensionar la imagen
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(picture_dir, picture_fn)

    # Redimensionar y guardar la imagen
    try:
        i = Image.open(form_picture)
        i.thumbnail(output_size, Image.LANCZOS)
        i.save(picture_path, quality=quality, optimize=True)
        logger.info(f"Imagen del contenedor guardada en: {picture_path}")
    except Exception as e:
        logger.error(f"Error al guardar la imagen del contenedor: {e}")
        raise

    return picture_fn

# Función para generar un código QR
def generate_qr(data, filename, output_size=(300, 300)):
    """Genera un código QR y lo guarda en el archivo especificado."""
    logger.debug(f"Generando QR para los datos: {data}")
    
    qr = qrcode.QRCode(
        version=1,  # Ajusta la versión según la cantidad de datos
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img = img.resize(output_size)

    try:
        img.save(filename)
        logger.info(f"QR guardado como {filename}")
    except Exception as e:
        logger.error(f"Error al guardar el QR: {e}")
        raise

# Función para guardar un código QR
def save_qr_image(data, container_name):
    """Guarda la imagen de un código QR generado para un contenedor."""
    # Limpiar el nombre del contenedor para evitar caracteres no válidos en nombres de archivos
    safe_container_name = re.sub(r'[^\w\s-]', '', container_name).strip().replace(' ', '_')

    qr_dir = os.path.join(current_app.root_path, 'static', 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)
    
    qr_path = os.path.join(qr_dir, f"{safe_container_name}.png")
    generate_qr(data, qr_path)
    
    return qr_path


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Solicitud de Restablecimiento de Contraseña', sender='admin@edefrutos.me', recipients=[user.email])
    msg.body = f'''Para restablecer tu contraseña, haz clic en el siguiente enlace:
{url_for('main.reset_token', token=token, _external=True)}

Si no solicitaste este cambio, simplemente ignora este mensaje.
'''
    try:
        mail.send(msg)
        logger.info(f"Correo de restablecimiento de contraseña enviado a {user.email}")
    except Exception as e:
        logger.error(f"Error al enviar correo de restablecimiento de contraseña: {e}")
        raise