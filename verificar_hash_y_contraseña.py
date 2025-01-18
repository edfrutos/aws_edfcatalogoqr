from app.models import User
from app.extensions import bcrypt

# Ajusta el correo y contraseña aquí
email = "tu_email@dominio.com"
password = "tu_contraseña"

# Obtener el usuario de la base de datos
user = User.objects(email=email).first()

# Verifica si el usuario existe
if user:
    # Verifica la contraseña
    if bcrypt.check_password_hash(user.password, password):
        print("Contraseña correcta")
    else:
        print("Contraseña incorrecta")
else:
    print("Usuario no encontrado")
