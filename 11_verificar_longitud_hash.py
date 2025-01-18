from mongoengine import connect, disconnect
from app.models import User

# Conectar a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"
disconnect()
connect(host=DB_URI)

# Recorrer todos los usuarios y verificar la longitud del hash de la contraseña
users = User.objects()
for user in users:
    if len(user.password) != 60:
        print(
            f"Usuario {user.username} tiene un hash de contraseña inválido: {user.password}"
        )
    else:
        print(f"Usuario {user.username} tiene un hash de contraseña válido")
