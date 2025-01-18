import os
import mongoengine as db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.connection import disconnect
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configurar la conexión a la base de datos
DB_URI = os.getenv("MONGO_URI")
if not DB_URI:
    raise ValueError("La URI de la base de datos no está configurada.")

try:
    disconnect()  # Desconectar si ya hay una conexión existente
    db.connect(host=DB_URI)
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit(1)


class User(db.Document):
    username = db.StringField(max_length=50, unique=True, required=True)
    email = db.StringField(max_length=50, unique=True, required=True)
    password = db.StringField(required=True)
    image_file = db.StringField(default="default.jpg")
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2:sha256:"):
            self.password = generate_password_hash(self.password)
        super().save(*args, **kwargs)


try:
    # Solicitar el nombre de usuario a eliminar
    nombre_usuario = input("Introduce el nombre de usuario que deseas eliminar: ")

    # Buscar el usuario en la base de datos
    usuario = User.objects(username=nombre_usuario).first()

    if usuario:
        # Eliminar el usuario
        usuario.delete()
        print(f"Usuario '{nombre_usuario}' eliminado exitosamente.")
    else:
        print(f"El usuario '{nombre_usuario}' no existe.")
except Exception as e:
    print(f"Error al eliminar el usuario: {e}")
finally:
    disconnect()  # Desconectar de la base de datos
