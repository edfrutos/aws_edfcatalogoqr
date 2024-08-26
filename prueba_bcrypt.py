# prueba_bcrypt.py
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def generar_hash_contrasena(contrasena):
    hashed = bcrypt.generate_password_hash(contrasena).decode('utf-8')
    return hashed

def verificar_contrasena(hashed_contrasena, contrasena):
    return bcrypt.check_password_hash(hashed_contrasena, contrasena)

# Prueba de generación de hash
contrasena = "mi_contrasena_segura"
hash_contrasena = generar_hash_contrasena(contrasena)
print(f"Hash de contraseña: {hash_contrasena}")

# Prueba de verificación de hash
es_correcta = verificar_contrasena(hash_contrasena, contrasena)
print(f"¿La contraseña es correcta? {'Sí' if es_correcta else 'No'}")