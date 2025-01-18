from mongoengine import connect, disconnect
from app.models import User
from app.extensions import bcrypt
from flask import Flask
from app.config import Config

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Conectar a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"
disconnect()
connect(host=DB_URI)

# Re-encriptar contraseñas no seguras
with app.app_context():
    users = User.objects()
    for user in users:
        # Verificar si la contraseña no está encriptada con bcrypt
        if not user.password.startswith("$2b$"):
            original_password = "contraseña_plana"  # Deberás obtener la contraseña original de alguna manera segura
            hashed_password = bcrypt.generate_password_hash(original_password).decode(
                "utf-8"
            )
            user.password = hashed_password
            user.save()
            print(f"Re-encriptada contraseña para usuario {user.username}")

print("Re-encriptación de contraseñas completada.")
