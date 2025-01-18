import os
import mongoengine as db
import certifi
from app.models import User
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
    db.connect(host=DB_URI, tlsCAFile=certifi.where())
    print("Conexión a la base de datos establecida.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit(1)

# Obtener un usuario para inspeccionar su contraseña
usuario = User.objects.first()  # Obtén el primer usuario o uno específico

if usuario:
    if usuario.password.startswith("pbkdf2:sha256:"):
        print("La contraseña está generada con werkzeug.security.")
    elif usuario.password.startswith("$2b$") or usuario.password.startswith("$2a$"):
        print("La contraseña está generada con bcrypt.")
    else:
        print("Formato de contraseña desconocido.")
else:
    print("No se encontró ningún usuario.")
