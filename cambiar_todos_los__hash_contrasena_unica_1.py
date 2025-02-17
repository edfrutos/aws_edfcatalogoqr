import os
import mongoengine as db
import bcrypt
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configurar la conexión a la base de datos
DB_URI = os.getenv("MONGO_URI")
if not DB_URI:
    raise ValueError("La URI de la base de datos no está configurada.")

try:
    db.disconnect()  # Desconectar si ya hay una conexión existente
    db.connect(host=DB_URI)
    print("Conexión a la base de datos establecida.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit(1)


class User(db.Document):
    username = db.StringField(max_length=50, unique=True, required=True)
    email = db.StringField(max_length=50, unique=True, required=True)
    password = db.StringField(required=True)
    image_file = db.StringField(default="default.jpg")
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)

    def set_password(self, password):
        # Generar un salt y crear el hash de la contraseña
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password):
        # Verificar la contraseña
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))


def update_passwords_with_unique_password(unique_password):
    try:
        # Iterar sobre todos los usuarios
        for usuario in User.objects:
            if usuario.password.startswith("pbkdf2:sha256:"):
                # Verificar la contraseña actual
                if check_password_hash(usuario.password, unique_password):
                    # Regenerar el hash de la contraseña con bcrypt
                    usuario.set_password(unique_password)
                    usuario.save()
                    print(
                        f"Contraseña para el usuario '{usuario.username}' actualizada a bcrypt."
                    )
                else:
                    print(
                        f"Error al verificar la contraseña para el usuario '{usuario.username}'."
                    )
    except Exception as e:
        print(f"Error al actualizar las contraseñas: {e}")
    finally:
        db.disconnect()  # Desconectar de la base de datos


if __name__ == "__main__":
    unique_password = input(
        "Introduce la contraseña única para actualizar los hashes: "
    )
    update_passwords_with_unique_password(unique_password)
