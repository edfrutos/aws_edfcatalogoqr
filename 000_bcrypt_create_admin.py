import os
import mongoengine as db
import bcrypt
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
        # Generar un salt y crear el hash de la contraseña
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        # Verificar la contraseña
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def save(self, *args, **kwargs):
        # No es necesario verificar el formato del hash con bcrypt
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
