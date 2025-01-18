import os
import mongoengine as db
import bcrypt
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
        # Generar un salt y crear el hash de la contraseña
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password):
        # Verificar la contraseña
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))

    def save(self, *args, **kwargs):
        # No es necesario verificar el prefijo del hash con bcrypt
        super().save(*args, **kwargs)


# Aquí puedes establecer los valores de nombre de usuario y contraseña
nombre_usuario = "edfadmin"
nueva_contrasena = "34Maf15si"

try:
    # Buscar el usuario en la base de datos
    usuario = User.objects(username=nombre_usuario).first()

    if usuario:
        # Regenerar el hash de la contraseña
        usuario.set_password(nueva_contrasena)
        usuario.save()
        print(
            f"Contraseña para el usuario '{nombre_usuario}' actualizada exitosamente."
        )
    else:
        print(f"El usuario '{nombre_usuario}' no existe.")
except Exception as e:
    print(f"Error al actualizar la contraseña: {e}")
finally:
    disconnect()  # Desconectar de la base de datos
