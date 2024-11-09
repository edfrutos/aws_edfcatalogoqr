<<<<<<< HEAD
# Crear una nueva cuenta de administrador
from app.models import User
admin = User(username='administrador', email='admin@example.com')
admin.set_password('34Maf15si')
admin.is_admin = True
admin.save()
=======
import os
import mongoengine as db
import bcrypt
from dotenv import load_dotenv
import certifi

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configurar la conexión a la base de datos
DB_URI = os.getenv("MONGO_URI")
if not DB_URI:
    raise ValueError("La URI de la base de datos no está configurada.")

try:
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
        super().save(*args, **kwargs)

try:
    # Verificar si el usuario 'edfcatalogo' ya existe
    existing_user = User.objects(username="edfcatalogo").first()

    if existing_user:
        print("El usuario 'edfcatalogo' ya existe. No se puede crear un duplicado.")
    else:
        # Crear el usuario si no existe
        new_user = User(
            username="edfcatalogo",
            email="catalogo@edfadmin.com",
            is_admin=False
        )
        new_user.set_password("34Maf15si")  # Asegúrate de reemplazar con la contraseña deseada
        new_user.save()
        print("Usuario 'edfcatalogo' creado exitosamente.")
except Exception as e:
    print(f"Error al crear el usuario: {e}")
finally:
    db.disconnect()  # Desconectar de la base de datos
>>>>>>> 595b5232ad9e12d7ef34de63e6e54e828cd9dbf4