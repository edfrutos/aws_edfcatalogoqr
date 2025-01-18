from pymongo import MongoClient

# Conectar a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(DB_URI)
db = client.get_database("app-qr-catalogacion")


def migrate_containers():
    containers_collection = db["container"]

    # Buscar todos los documentos que tienen el campo 'image_file'
    containers = containers_collection.find({"image_file": {"$exists": True}})

    for container in containers:
        print(f"Migrating container: {container['name']}")

        # Convertir el campo 'image_file' a 'image_files'
        image_files = [container["image_file"]]

        # Actualizar el documento
        containers_collection.update_one(
            {"_id": container["_id"]},
            {"$set": {"image_files": image_files}, "$unset": {"image_file": ""}},
        )


if __name__ == "__main__":
    migrate_containers()
    print("Migration completed.")
