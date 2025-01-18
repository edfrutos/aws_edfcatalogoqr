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


def check_user_type(username):
    try:
        user = User.objects(username=username).first()
        if user:
            if user.is_admin:
                print(f"El usuario '{username}' es un administrador.")
            else:
                print(f"El usuario '{username}' es un usuario normal.")
        else:
            print(f"El usuario '{username}' no existe en la base de datos.")
    except Exception as e:
        print(f"Error al verificar el tipo de usuario: {e}")


# Reemplaza 'nombre_usuario' con el nombre de usuario que deseas verificar
nombre_usuario = "edefrutos"
check_user_type(nombre_usuario)
