import bcrypt
from mongoengine import disconnect
from app import create_app
from app.models import User

# Desconectar cualquier conexión previa
disconnect()

# Crear una nueva aplicación Flask y conectar a la base de datos
app = create_app()
app.app_context().push()

# Iterar sobre todos los usuarios y actualizar sus contraseñas
for user in User.objects:
    try:
        # Intentar verificar la contraseña con el formato antiguo
        if not bcrypt.checkpw("test_password".encode('utf-8'), user.password.encode('utf-8')):
            # Si falla, generamos un nuevo hash para la contraseña existente
            new_hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.password = new_hashed_password
            user.save()
            print(f"Contraseña actualizada para el usuario: {user.username}")
    except ValueError:
        # Si ocurre un ValueError, significa que la contraseña está en el formato antiguo
        new_hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password = new_hashed_password
        user.save()
        print(f"Contraseña actualizada para el usuario: {user.username}")

print("Actualización de contraseñas completada.")