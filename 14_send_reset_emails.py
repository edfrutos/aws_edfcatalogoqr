import os
from flask import Flask, url_for
from flask_mail import Message
from app.models import User
from app.extensions import mail
from app.config import Config
from dotenv import load_dotenv
from mongoengine import connect, disconnect

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Conectar a la base de datos
DB_URI = os.getenv('MONGO_URI')
disconnect()
connect(host=DB_URI)

# Función para enviar correo de restablecimiento de contraseña
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Solicitud de restablecimiento de contraseña',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{url_for('main.change_pass', token=token, _external=True)}

Si no solicitaste este cambio, simplemente ignora este mensaje y no se realizará ningún cambio.
'''
    with app.app_context():
        mail.send(msg)

# Script para enviar correos de restablecimiento
with app.app_context():
    users = User.objects()
    for user in users:
        if not user.password.startswith("$2b$"):
            send_reset_email(user)
            print(f"Correo de restablecimiento enviado a {user.username}")

print("Envío de correos de restablecimiento completado.")