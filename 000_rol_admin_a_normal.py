import mongoengine as db
from mongoengine.connection import disconnect
from dotenv import load_dotenv
import os

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
    image_file = db.StringField(default='default.jpg')
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)

def cambiar_rol_usuario():
    nombre_usuario = input("Introduce el nombre de usuario que deseas cambiar a rol normal: ")

    try:
        # Buscar el usuario en la base de datos
        usuario = User.objects(username=nombre_usuario).first()

        if usuario:
            if usuario.is_admin:
                usuario.is_admin = False
                usuario.save()
                print(f"El usuario '{nombre_usuario}' ahora es un usuario normal.")
            else:
                print(f"El usuario '{nombre_usuario}' ya es un usuario normal.")
        else:
            print(f"El usuario '{nombre_usuario}' no existe.")
    except Exception as e:
        print(f"Error al cambiar el rol del usuario: {e}")
    finally:
        disconnect()  # Desconectar de la base de datos

if __name__ == "__main__":
    cambiar_rol_usuario()
