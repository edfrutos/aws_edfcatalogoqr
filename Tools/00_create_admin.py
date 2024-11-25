import mongoengine as db
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.connection import disconnect

# Configurar la conexión a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"
disconnect()  # Desconectar si ya hay una conexión existente
db.connect(host=DB_URI)

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

# Verificar si el usuario admin ya existe
existing_admin = User.objects(username="administrador").first()

if existing_admin:
    print("El usuario 'administrador' ya existe.")
else:
    # Crear el usuario admin
    admin_user = User(
        username="administrador",
        email="admin@example.com",
        is_admin=True
    )
    admin_user.set_password("adminpassword")
    admin_user.save()
    print("Usuario 'administrador' creado exitosamente.")