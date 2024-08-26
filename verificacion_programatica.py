from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash
import re
import mongoengine

# Desconectar cualquier conexión existente
mongoengine.disconnect(alias='default')

app = create_app()

with app.app_context():
    users = User.objects()
    bcrypt_regex = re.compile(r'^\$2b\$12\$[./A-Za-z0-9]{53}$')
    
    for user in users:
        if not bcrypt_regex.match(user.password):
            print(f"Password for user {user.username} is not in the expected bcrypt format.")
        else:
            print(f"Password for user {user.username} is correctly formatted.")