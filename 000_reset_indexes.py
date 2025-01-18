# reset_indexes.py
from mongoengine import connect
from app.models import Container
import pymongo


def reset_indexes():
    # Conectar a la base de datos
    connect("app-qr-catalogacion")

    try:
        # Eliminar todos los índices excepto el _id
        Container._get_collection().drop_indexes()
        print("Índices eliminados correctamente")

        # Recrear los índices definidos en el modelo
        Container.ensure_indexes()
        print("Índices recreados correctamente")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    reset_indexes()
