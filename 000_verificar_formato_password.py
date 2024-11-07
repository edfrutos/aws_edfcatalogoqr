import os
import mongoengine as db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.connection import disconnect
from mongoengine import connect
from app.models import User
from app.models import Container
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

# Obtener un usuario para inspeccionar su contraseña
usuario = User.objects.first()  # Obtén el primer usuario o uno específico

if usuario:
    print(f"Formato de la contraseña: {usuario.password}")
else:
    print("No se encontró ningún usuario.")
