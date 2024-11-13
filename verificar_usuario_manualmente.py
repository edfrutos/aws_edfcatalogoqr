import os
from mongoengine import disconnect, connect
from app.models import User

# Configurar la conexión a la base de datos
DB_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/edfcatalogoqr")
try:
    disconnect()  # Desconectar cualquier conexión previa
    connect(host=DB_URI)
    print("Conexión establecida con MongoDB.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit(1)

# Solicitar username o email del usuario a verificar
identificador_usuario = input("Introduce el 'username' o 'email' del usuario a verificar: ")

try:
    # Buscar usuario por 'email' o 'username'
    usuario = User.objects(email=identificador_usuario).first() or User.objects(username=identificador_usuario).first()

    # Mostrar información del usuario si se encuentra
    if usuario:
        print(f"Username: {usuario.username}, Email: {usuario.email}, Admin: {usuario.is_admin}")
    else:
        print("No se encontró el usuario.")
except Exception as e:
    print(f"Error al buscar el usuario: {e}")
finally:
    disconnect(alias='default')
    print("Conexión a MongoDB cerrada.")