from mongoengine import connect, disconnect
from app.models import Container

# Conectar a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority&appName=Cluster0"

# Desconectar si ya hay una conexión
disconnect()

# Conectar a la base de datos
connect(host=DB_URI)


# Migrar documentos Container
def migrate_containers():
    containers = Container.objects()

    for container in containers:
        if hasattr(container, "image_file"):
            print(f"Migrating container: {container.name}")
            container.image_files = [container.image_file]
            del container.image_file

            container.save()


if __name__ == "__main__":
    migrate_containers()
    print("Migration completed.")
