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

# Configuración de Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('logs/utils.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning("Acceso denegado. Usuario no es administrador.")
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

def save_profile_picture(form_picture, folder='profile_pics', output_size=(125, 125)):
    """Guarda una foto de perfil redimensionada."""
    if not isinstance(form_picture, FileStorage):
        logger.error("El objeto proporcionado no es un archivo válido")
        raise ValueError("El objeto proporcionado no es un archivo válido")

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', folder, picture_fn)

    # Redimensionar la imagen
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    logger.info(f"Foto de perfil guardada en: {picture_path}")
    return picture_fn

def save_container_picture(form_picture, folder='container_pics', output_size=(800, 800)):
    """Guarda una imagen del contenedor redimensionada."""
    if not isinstance(form_picture, FileStorage):
        logger.error("El objeto proporcionado no es un archivo válido")
        raise ValueError("El objeto proporcionado no es un archivo válido")

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext

    picture_dir = os.path.join(current_app.root_path, 'static', folder)
    if not os.path.exists(picture_dir):
        logger.info(f"Creando el directorio: {picture_dir}")
        os.makedirs(picture_dir)

    picture_path = os.path.join(picture_dir, picture_fn)

    # Redimensionar la imagen
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    logger.info(f"Imagen del contenedor guardada en: {picture_path}")
    return picture_fn

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
    img.save(filename)

    logger.info(f"QR guardado como {filename}")

def save_qr_image(data, container_name):
    """Guarda la imagen de un código QR generado para un contenedor."""
    qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container_name + '.png')
    generate_qr(data, qr_path)
    return qr_path

def send_reset_email(user):
    """Envía un correo electrónico para restablecer la contraseña del usuario."""
    token = user.get_reset_token()
    msg = Message('Solicitud de restablecimiento de contraseña', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{url_for('main.reset_token', token=token, _external=True)}

Si no solicitaste este cambio, simplemente ignora este mensaje.
'''
    mail.send(msg)
    logger.info(f"Correo de restablecimiento de contraseña enviado a {user.email}")