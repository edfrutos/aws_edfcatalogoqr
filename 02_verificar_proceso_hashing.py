import bcrypt

def set_password(password):
    # Generar un hash seguro para la contraseña
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(stored_password, provided_password):
    # Verificar la contraseña proporcionada contra el hash almacenado
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
