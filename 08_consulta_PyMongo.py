import pymongo
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "app-qr-catalogacion"
COLLECTION_NAME = "user"


def list_users():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        print(f"Conectado a la base de datos: {db.name}")
        print(f"Usando la colección: {collection.name}")

        users = collection.find()
        users_list = list(users)

        if not users_list:
            print("No se encontraron usuarios en la colección.")

        print(f"Usuarios encontrados: {len(users_list)}")
        for user in users_list:
            print(
                f"Usuario: {user.get('username')}, Email: {user.get('email')}, Admin: {user.get('is_admin')}"
            )
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Conexión exitosa a MongoDB")
    list_users()
