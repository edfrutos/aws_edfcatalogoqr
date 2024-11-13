import os
from mongoengine import connect, disconnect
from app.models import User
from app.extensions import bcrypt

# Configurar la conexión a MongoDB
try:
    disconnect()  # Desconectar cualquier conexión previa
    connect(
        host=os.environ.get('MONGO_URI', 'mongodb://localhost:27017/edfcatalogoqr'),
        alias='default'
    )
    print("Conexión establecida con MongoDB.")
except Exception as e:
    print("Error al conectar a MongoDB:", e)
    exit(1)

# Registrar el usuario
try:
    # Generar hash de la contraseña
    hashed_password = bcrypt.generate_password_hash("15si34Maf").decode('utf-8')
    
    # Crear el objeto usuario y guardarlo en la base de datos
    user = User(username="Agustin", email="agustin@gmail.com", password=hashed_password)
    user.save()
    print("Usuario registrado correctamente:", user)
except Exception as e:
    print("Error al registrar el usuario:", e)

# Cerrar la conexión (opcional)
finally:
    disconnect(alias='default')
    print("Conexión a MongoDB cerrada.")