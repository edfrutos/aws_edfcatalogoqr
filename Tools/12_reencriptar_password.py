from app import create_app
from app.models import User
from app.extensions import bcrypt

app = create_app()

with app.app_context():
    users = User.objects()
    for user in users:
        if len(user.password) != 60:
            # Supongamos que tienes acceso a las contraseñas originales de alguna manera
            # Esto es solo un ejemplo. En la práctica, necesitarás pedir a los usuarios que restablezcan sus contraseñas.
            original_password = "contraseña_plana"  # Esto debería ser reemplazado por la forma correcta de obtener la contraseña original
            hashed_password = bcrypt.generate_password_hash(original_password).decode(
                "utf-8"
            )
            user.password = hashed_password
            user.save()
            print(f"Re-encriptada contraseña para usuario {user.username}")
