from app import create_app
from app.models import User
from mongoengine import connect

app = create_app()
connect(db='nombre_de_tu_base_de_datos', host='localhost', port=27017)

with app.app_context():
    users = User.objects()
    for user in users:
        if not hasattr(user, 'address'):
            user.address = ''  # O cualquier valor predeterminado
            user.save()