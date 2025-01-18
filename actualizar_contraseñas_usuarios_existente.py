from werkzeug.security import generate_password_hash
from app.models import User
from mongoengine import connect, disconnect

# Conecta a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority&appName=Cluster0"
disconnect()
connect(host=DB_URI)

# Actualiza las contraseñas de los usuarios existentes
users = User.objects()
for user in users:
    if user.password and "$pbkdf2-sha256$" not in user.password:
        user.password = generate_password_hash(
            user.password, method="pbkdf2:sha256", salt_length=8
        )
        user.save()

print("Contraseñas actualizadas correctamente.")
