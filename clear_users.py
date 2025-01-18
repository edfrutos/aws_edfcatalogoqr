# clear_users.py
from app import create_app
from app.models import User
from mongoengine import disconnect

# Desconectar si ya hay una conexión
disconnect()

app = create_app()

with app.app_context():
    User.objects.delete()
    print("Todos los usuarios han sido eliminados de la base de datos.")
