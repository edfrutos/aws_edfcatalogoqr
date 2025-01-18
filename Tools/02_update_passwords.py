import mongoengine as db
from werkzeug.security import generate_password_hash, check_password_hash

DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"
from mongoengine.connection import disconnect

# Disconnect if already connected
disconnect()

db.connect(host=DB_URI)


class User(db.Document):
    username = db.StringField(max_length=50, unique=True, required=True)
    email = db.StringField(max_length=50, unique=True, required=True)
    password = db.StringField(required=True)
    image_file = db.StringField(default="default.jpg")
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)

    def set_password(self, password):
        print(f"Setting password for user {self.username}")
        self.password = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=8
        ).decode("utf-8")

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2:sha256"):
            print(f"Encrypting password for user {self.username}")
            self.password = generate_password_hash(
                self.password, method="pbkdf2:sha256", salt_length=8
            ).decode("utf-8")
        super().save(*args, **kwargs)


def update_user_passwords():
    try:
        users = User.objects()
        print(f"Usuarios encontrados: {len(users)}")
        for user in users:
            if user.password:
                print(f"Usuario {user.username} tiene una contraseña: {user.password}")
            else:
                print(f"Usuario {user.username} NO tiene una contraseña.")
            if user.password and not user.password.startswith("pbkdf2:sha256"):
                print(f"Actualizando contraseña para: {user.username}")
                original_password = user.password  # Guardar la contraseña original
                user.set_password(user.password)
                user.save()
                # Verificar si la contraseña se ha actualizado
                if user.password != original_password:
                    print(f"Contraseña actualizada para el usuario {user.username}")
                else:
                    print(
                        f"Error al actualizar la contraseña para el usuario {user.username}"
                    )
    except db.errors.FieldDoesNotExist as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")


if __name__ == "__main__":
    update_user_passwords()
