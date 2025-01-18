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

# Solicitar el nombre de usuario o correo electrónico
identificador_usuario = input(
    "Introduce el nombre de usuario o correo electrónico del usuario a convertir en administrador: "
)

try:
    # Buscar el usuario por nombre de usuario o correo electrónico
    usuario = (
        User.objects(email=identificador_usuario).first()
        or User.objects(username=identificador_usuario).first()
    )

    if usuario:
        # Cambiar el rol a administrador
        usuario.is_admin = True
        usuario.save()
        print(f"El usuario '{usuario.username}' ahora es administrador.")
    else:
        print("Usuario no encontrado.")
except Exception as e:
    print("Error al actualizar el rol del usuario:", e)
finally:
    disconnect(alias="default")
    print("Conexión a MongoDB cerrada.")
