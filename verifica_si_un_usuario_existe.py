import os
from mongoengine import connect, disconnect
from app.models import User

# Conectar a MongoDB
try:
    disconnect()  # Desconectar cualquier conexión previa
    connect(
        host=os.environ.get("MONGO_URI", "mongodb://localhost:27017/edfcatalogoqr"),
        alias="default",
    )
    print("Conexión establecida con MongoDB.")
except Exception as e:
    print("Error al conectar a MongoDB:", e)
    exit(1)

# Buscar el usuario por correo electrónico
email_a_buscar = "edfrutos@gmail.com"  # Cambia esto al email que deseas verificar

try:
    usuario = User.objects(email=email_a_buscar).first()
    if usuario:
        print("Usuario encontrado:")
        print(f"Username: {usuario.username}")
        print(f"Email: {usuario.email}")
        print(
            f"Es administrador: {usuario.is_admin}"
        )  # Muestra si el usuario es administrador (si tienes este campo)
        print(
            f"Imagen de perfil: {usuario.image_file}"
        )  # Muestra la imagen de perfil (si tienes este campo)
    else:
        print("Usuario no encontrado.")
except Exception as e:
    print("Error al buscar el usuario:", e)
finally:
    disconnect(alias="default")
    print("Conexión a MongoDB cerrada.")
