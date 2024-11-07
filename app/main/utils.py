import os
import secrets
from PIL import Image,UnidentifiedImageError
from flask import current_app, url_for
from flask_mail import Message
from app import mail
import qrcode

def save_picture(form_picture):
    try:
        # Verificar si el archivo es una imagen
        i = Image.open(form_picture)
        i.verify()  # Verifica que el archivo sea una imagen válida

        # Generar un nombre aleatorio para la imagen
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

        # Redimensionar la imagen antes de guardarla
        output_size = (800, 800)  # Aumentar la resolución
        i.thumbnail(output_size)
        i.save(picture_path)

        return picture_fn
    
    except UnidentifiedImageError:
        raise ValueError("El archivo subido no es una imagen válida.")
    except Exception as e:
        # Manejo de otros errores
        raise RuntimeError(f"Error al guardar la imagen: {e}")

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Solicitud de restablecimiento de contraseña',
                  sender='admin@edefrutos.me',
                  recipients=[user.email])
    msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{url_for('main.change_pass', token=token, _external=True)}

Si no solicitaste este cambio, simplemente ignora este mensaje y no se realizará ningún cambio.
'''
    mail.send(msg)

def save_qr_image(data, container_name):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # Make QR code larger
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container_name + '.png')
    img.save(qr_path)
    return qr_path