import os
import mongoengine as db
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configurar la conexión a la base de datos
DB_URI = os.getenv("MONGO_URI")
if not DB_URI:
    raise ValueError("La URI de la base de datos no está configurada.")

try:
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


def make_user_admin(username):
    try:
        # Buscar el usuario en la base de datos
        usuario = User.objects(username=username).first()

        if usuario:
            # Cambiar el estado a administrador
            usuario.is_admin = True
            usuario.save()
            print(f"El usuario '{username}' ahora es administrador.")
        else:
            print(f"El usuario '{username}' no existe.")
    except Exception as e:
        print(f"Error al cambiar el tipo de usuario: {e}")
    finally:
        db.disconnect()  # Desconectar de la base de datos


# Cambia 'nombre_usuario' por el nombre de usuario que deseas actualizar
nombre_usuario = "edfadmin"
make_user_admin(nombre_usuario)
