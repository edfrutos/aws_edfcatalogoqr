import os
import mongoengine as db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.connection import disconnect
from dotenv import load_dotenv
import certifi

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

class User(db.Document):
    username = db.StringField(max_length=50, unique=True, required=True)
    email = db.StringField(max_length=50, unique=True, required=True)
    password = db.StringField(required=True)
    image_file = db.StringField(default='default.jpg')
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2:sha256:'):
            self.password = generate_password_hash(self.password)
        super().save(*args, **kwargs)

try:
    # Verificar si el usuario admin ya existe
    existing_admin = User.objects(username="edfadmin").first()

    if existing_admin:
        print("El usuario 'edfadmin' ya existe.")
    else:
        # Crear el usuario admin
        admin_user = User(
            username="edfadmin",
            email="admin@edfadmin.com",
            is_admin=True
        )
        admin_user.set_password("34Maf15si")
        admin_user.save()
        print("Usuario 'edfadmin' creado exitosamente.")
except Exception as e:
    print(f"Error al crear el usuario edfadmin: {e}")
finally:
    disconnect()  # Desconectar de la base de datos
