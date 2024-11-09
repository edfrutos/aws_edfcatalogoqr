import os
from dotenv import load_dotenv
from mongoengine import connect, disconnect
from app.models import User

# Cargar variables de entorno
load_dotenv()

# Desconectar si ya hay una conexión existente
disconnect()

# Conectar a MongoDB
DB_URI = os.getenv("MONGO_URI")
print(f"Conectando a MongoDB en: {DB_URI}")
connect(host=DB_URI)
print("Conexión a MongoDB establecida.")

def listar_usuarios():
    users = User.objects()
    print(f"Usuarios encontrados: {len(users)}")
    for user in users:
        print(f"Usuario: {user.username}, Email: {user.email}, Admin: {user.is_admin}")

if __name__ == "__main__":
    listar_usuarios()