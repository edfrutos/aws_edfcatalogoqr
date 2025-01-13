import os
import secrets
from PIL import Image, ImageDraw
from flask import current_app, url_for, flash, redirect, request, abort
from werkzeug.datastructures import FileStorage
import qrcode
from flask_mail import Message
from app.extensions import mail
from functools import wraps
from flask_login import current_user
import logging
import logging.handlers
import re
import unicodedata
from typing import Optional, Tuple, Union, Callable, Any
from pathlib import Path

# Configuración de Logging
logger = logging.getLogger('app.utils')
logger.setLevel(logging.INFO)

# Asegurar que el directorio de logs existe
Path('logs').mkdir(exist_ok=True)

# Configurar RotatingFileHandler para mejor manejo de logs
handler = logging.handlers.RotatingFileHandler(
    'logs/app.log',
    maxBytes=1024 * 1024,  # 1MB
    backupCount=5,
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def handle_errors(f: Callable) -> Callable:
    """
    Decorador para manejar errores de forma consistente en las rutas.
    
    Args:
        f: Función a decorar
    
    Returns:
        Callable: Función decorada con manejo de errores
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Error de validación: {str(e)}")
            flash(str(e), 'warning')
        except FileNotFoundError as e:
            logger.error(f"Archivo no encontrado: {str(e)}")
            flash('Error: Archivo no encontrado', 'danger')
        except PermissionError as e:
            logger.error(f"Error de permisos: {str(e)}")
            flash('Error: Permisos insuficientes', 'danger')
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            flash('Ha ocurrido un error inesperado', 'danger')
        
        return redirect(request.referrer or url_for('main.home'))
    
    return decorated_function

def ensure_folder_exists(folder_path: Union[str, Path]) -> None:
    """
    Asegura que una carpeta existe y tiene los permisos correctos.
    
    Args:
        folder_path: Ruta de la carpeta a verificar/crear
    """
    try:
        Path(folder_path).mkdir(parents=True, mode=0o755, exist_ok=True)
        logger.debug(f"Carpeta verificada/creada: {folder_path}")
    except Exception as e:
        logger.error(f"Error al crear carpeta {folder_path}: {e}")
        raise

def create_default_image() -> None:
    """Crea una imagen por defecto si no existe."""
    default_image_path = Path(current_app.root_path) / 'static' / 'container_pics' / 'default.png'
    
    if not default_image_path.exists():
        try:
            img = Image.new('RGB', (200, 200), color='gray')
            d = ImageDraw.Draw(img)
            d.text((70, 90), "No imagen", fill='white')
            img.save(default_image_path)
            logger.info("Imagen por defecto creada exitosamente")
        except Exception as e:
            logger.error(f"Error creando imagen por defecto: {e}")
            raise

def admin_required(func):
    """
    Decorador que verifica si el usuario actual es administrador.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(f"Intento de acceso no autorizado a {func.__name__}")
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

def normalize_name(name: str) -> str:
    """
    Normaliza un nombre eliminando acentos y caracteres especiales.
    
    Args:
        name: Nombre a normalizar
    
    Returns:
        str: Nombre normalizado
    """
    if not isinstance(name, str):
        raise ValueError("El nombre debe ser una cadena de texto")
    
    name = name.strip()
    name = " ".join(name.split())
    name_normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()
    name_normalized = re.sub(r'[^a-z0-9]+', ' ', name_normalized).strip()
    return name_normalized

def save_picture(
    form_picture: FileStorage,
    folder: str,
    output_size: Tuple[int, int],
    quality: int = 85
) -> str:
    """
    Guarda y procesa una imagen.
    
    Args:
        form_picture: Archivo de imagen
        folder: Carpeta destino
        output_size: Tamaño de salida (ancho, alto)
        quality: Calidad de la imagen (1-100)
    
    Returns:
        str: Nombre del archivo guardado
    """
    if not isinstance(form_picture, FileStorage):
        raise ValueError("El objeto proporcionado no es un archivo válido")

    picture_dir = Path(current_app.root_path) / 'static' / folder
    ensure_folder_exists(picture_dir)

    try:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = f"{random_hex}{f_ext}"
        picture_path = picture_dir / picture_fn

        with Image.open(form_picture) as img:
            img.thumbnail(output_size, Image.LANCZOS)
            img.save(picture_path, quality=quality, optimize=True)

        if not picture_path.exists():
            raise FileNotFoundError("La imagen no se guardó correctamente")

        logger.info(f"Imagen guardada exitosamente en: {picture_path}")
        return picture_fn

    except Exception as e:
        logger.error(f"Error al guardar la imagen: {e}")
        raise

def save_profile_picture(form_picture: FileStorage) -> str:
    """Guarda una foto de perfil."""
    return save_picture(form_picture, 'profile_pics', (300, 300), 90)

def save_container_picture(form_picture: FileStorage) -> str:
    """Guarda una imagen de contenedor."""
    create_default_image()
    return save_picture(form_picture, 'container_pics', (800, 800), 85)

def generate_qr(
    data: str,
    filename: Union[str, Path],
    output_size: Tuple[int, int] = (300, 300)
) -> bool:
    """
    Genera un código QR y lo guarda.
    
    Args:
        data: Datos a codificar en el QR
        filename: Ruta donde guardar el QR
        output_size: Tamaño de salida del QR
    
    Returns:
        bool: True si se generó correctamente
    """
    logger.debug(f"Generando QR para: {data}")
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img = img.resize(output_size)
        
        # Asegurar que el directorio existe
        ensure_folder_exists(Path(filename).parent)
        
        img.save(filename)
        
        if not Path(filename).exists():
            raise FileNotFoundError("El código QR no se guardó correctamente")
            
        logger.info(f"QR generado exitosamente: {filename}")
        return True

    except Exception as e:
        logger.error(f"Error al generar/guardar el QR: {e}")
        raise

def save_qr_image(data: str, container_name: str) -> Path:
    """
    Guarda la imagen de un código QR para un contenedor.
    
    Args:
        data: Datos a codificar en el QR
        container_name: Nombre del contenedor
    
    Returns:
        Path: Ruta del archivo QR generado
    """
    safe_container_name = re.sub(r'[^\w\s-]', '', container_name).strip().replace(' ', '_')
    qr_dir = Path(current_app.root_path) / 'static' / 'qr_codes'
    ensure_folder_exists(qr_dir)
    
    qr_path = qr_dir / f"{safe_container_name}.png"
    generate_qr(data, qr_path)
    
    return qr_path

def send_reset_email(user) -> None:
    """
    Envía un correo electrónico para restablecer la contraseña.
    
    Args:
        user: Usuario que solicita el reset
    
    Raises:
        Exception: Si hay error al enviar el correo
    """
    try:
        salt = current_app.config.get('SECURITY_PASSWORD_SALT')
        if not salt:
            raise ValueError("SECURITY_PASSWORD_SALT no está definido")
        token = user.get_reset_token()
        msg = Message(
            'Solicitud de Restablecimiento de Contraseña',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        msg.body = f'''Para restablecer tu contraseña, haz clic en el siguiente enlace:
{url_for('users.reset_token', token=token, _external=True)}

Si no solicitaste este cambio, simplemente ignora este mensaje.

Este enlace expirará en 30 minutos.
'''
        mail.send(msg)
        logger.info(f"Correo de restablecimiento enviado a {user.email}")
        
    except KeyError as e:
        logger.error(f"Error al enviar correo de restablecimiento: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al enviar correo de restablecimiento: {e}")
        raise

def verify_image_path(image_path: Union[str, Path]) -> bool:
    """
    Verifica si una ruta de imagen existe y es accesible.
    
    Args:
        image_path: Ruta de la imagen a verificar
    
    Returns:
        bool: True si la imagen existe y es accesible
    """
    try:
        path = Path(image_path)
        return path.exists() and os.access(path, os.R_OK)
    except Exception as e:
        logger.error(f"Error verificando ruta de imagen {image_path}: {e}")
        return False

def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Elimina un archivo de forma segura.
    
    Args:
        file_path: Ruta del archivo a eliminar
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info(f"Archivo eliminado: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error al eliminar archivo {file_path}: {e}")
        return False

def get_file_extension(filename: str) -> str:
    """
    Obtiene la extensión de un archivo de forma segura.
    
    Args:
        filename: Nombre del archivo
    
    Returns:
        str: Extensión del archivo (con el punto)
    """
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Verifica si un archivo tiene una extensión permitida.
    
    Args:
        filename: Nombre del archivo
        allowed_extensions: Conjunto de extensiones permitidas
    
    Returns:
        bool: True si la extensión está permitida
    """
    return get_file_extension(filename) in allowed_extensions

# Constantes útiles
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB