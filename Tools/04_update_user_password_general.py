import mongoengine as db
from flask_bcrypt import Bcrypt

DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"
from mongoengine.connection import disconnect

# Desconectar si ya hay una conexión existente
disconnect()

# Conectar a la base de datos
db.connect(host=DB_URI)
bcrypt = Bcrypt()


class User(db.Document):
    username = db.StringField(max_length=50, unique=True, required=True)
    email = db.StringField(max_length=50, unique=True, required=True)
    password = db.StringField(required=True)
    image_file = db.StringField(default="default.jpg")
    address = db.StringField()
    phone = db.StringField()
    is_admin = db.BooleanField(default=False)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")


def update_passwords(new_password):
    users = User.objects()
    print(f"Usuarios encontrados: {len(users)}")
    for user in users:
        print(f"Actualizando contraseña para: {user.username}")
        user.set_password(new_password)
        user.save()
        print(f"Contraseña actualizada para el usuario {user.username}")


if __name__ == "__main__":
    print("Conexión exitosa a MongoDB")
    new_password = input("Introduce la nueva contraseña para todos los usuarios: ")
    update_passwords(new_password)
