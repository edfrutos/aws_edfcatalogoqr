import os
from dotenv import load_dotenv
from mongoengine import connect, disconnect
from mongoengine.errors import DoesNotExist
from getpass import getpass
from app.models import User

# Cargar variables de entorno
load_dotenv()

# Verificar valores de las variables de entorno
print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")
print(f"MONGO_URI: {os.getenv('MONGO_URI')}")
print(f"EMAIL_USER: {os.getenv('EMAIL_USER')}")
print(f"EMAIL_PASS: {os.getenv('EMAIL_PASS')}")

# Desconectar si ya hay una conexión existente
disconnect()

# Conectar a MongoDB
DB_URI = os.getenv("MONGO_URI")
connect(host=DB_URI)
print("Conexión a MongoDB establecida.")


def update_password(username, new_password):
    try:
        user = User.objects.get(username=username)
        print(f"Usuario encontrado: {user.username}")
        user.set_password(new_password)
        user.save()
        print(f"Contraseña actualizada para el usuario {username}")
    except DoesNotExist:
        print(f"Usuario {username} no encontrado.")
    except Exception as e:
        print(f"Error inesperado: {e}")


def main():
    username = input("Introduce el nombre de usuario: ")
    new_password = getpass("Introduce la nueva contraseña: ")
    update_password(username, new_password)


if __name__ == "__main__":
    main()
