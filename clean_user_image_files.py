from app import create_app
from app.models import User
from mongoengine import connect, disconnect

app = create_app()

with app.app_context():
    # Desconectar cualquier conexión activa
    disconnect()

    # Obtén la URI directamente de la configuración de Flask
    db_uri = app.config['MONGODB_SETTINGS']['host']

    # Conectar a MongoDB
    connection = connect(host=db_uri)
    db = connection.get_database()  # Obtener la base de datos actual
    collection = db[User._meta['collection']]  # Acceder a la colección de User

    # Buscar y eliminar el campo "image_files" de los documentos
    result = collection.update_many(
        {"image_files": {"$exists": True}},  # Filtrar documentos con el campo "image_files"
        {"$unset": {"image_files": ""}}     # Eliminar el campo "image_files"
    )

    print(f"Documentos modificados: {result.modified_count}")
