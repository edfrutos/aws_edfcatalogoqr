import os
import mongoengine as db
import bcrypt
import certifi
from app.models import User
from mongoengine.connection import disconnect
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configurar la conexión a la base de datos
DB_URI = os.getenv("MONGO_URI")
if not DB_URI:
    raise ValueError("La URI de la base de datos no está configurada.")

try:
    disconnect()  # Desconectar si ya hay una conexión existente
    db.connect(host=DB_URI, tlsCAFile=certifi.where())
    print("Conexión a la base de datos establecida.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit(1)
bcrypt = Bcrypt()


class User(db.Document):
    username = db.StringField(max_length=50, unique=True, required=True)
    email = db.StringField(max_length=50, unique=True, required=True)
    password = db.StringField(required=True)
    image_file = db.StringField(default="default.jpg")
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")


def update_passwords(new_password):
    users = User.objects()
    print(f"Usuarios encontrados: {len(users)}")
    for user in users:
        print(f"Actualizando contraseña para: {user.username}")
        user.set_password(new_password)
        user.save()
        print(f"Contraseña actualizada para el usuario {user.username}")


if __name__ == "__main__":
    print("Conexión exitosa a MongoDB")
    new_password = input("Introduce la nueva contraseña para todos los usuarios: ")
    update_passwords(new_password)
