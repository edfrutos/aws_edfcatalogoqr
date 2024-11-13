import bcrypt
from mongoengine import connect, Document, StringField

# Conectar a la base de datos
connect('app-qr-catalogacion')

class User(Document):
    username = StringField(max_length=50, unique=True, required=True)
    password = StringField(required=True)

def regenerate_password_hash(username, new_password):
    user = User.objects(username=username).first()
    if user:
        # Generar un nuevo hash para la contraseña
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.password = hashed.decode('utf-8')
        user.save()
        print(f"Hash de la contraseña para el usuario '{username}' regenerado y almacenado correctamente.")
    else:
        print(f"Usuario '{username}' no encontrado.")

# Ejemplo de uso
regenerate_password_hash('edfadmin', '34Maf15si')
