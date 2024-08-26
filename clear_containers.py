from app import create_app
from app.models import Container
from mongoengine import disconnect

# Desconectar si ya hay una conexión
disconnect()

app = create_app()

with app.app_context():
    # Eliminar todos los contenedores
    Container.objects.delete()
    print("Todos los contenedores han sido eliminados de la base de datos.")