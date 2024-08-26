import logging
from itsdangerous import TimedSerializer as Serializer
from flask_login import UserMixin
from flask import current_app
from mongoengine import Document, StringField, ListField, BooleanField, ReferenceField, connect, disconnect
from app.extensions import login_manager, bcrypt

# Configuración de Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('logs/models.log')
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# URI de conexión a la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"

# Desconectar si ya hay una conexión existente
try:
    disconnect()
    logger.info("Desconexión exitosa de la base de datos anterior.")
except Exception as e:
    logger.warning(f"No se pudo desconectar: {e}")

# Conectar a la base de datos
try:
    connect(host=DB_URI)
    logger.info("Conectado a la base de datos.")
except Exception as e:
    logger.error(f"Error conectando a la base de datos: {e}")

@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario por ID para Flask-Login."""
    logger.debug(f"Cargando usuario con ID: {user_id}")
    return User.objects(id=user_id).first()

class User(Document, UserMixin):
    username = StringField(max_length=50, unique=True, required=True)
    email = StringField(max_length=50, unique=True, required=True)
    password = StringField(required=True)
    image_file = StringField(default='default.jpg')
    address = StringField()
    phone = StringField()
    is_admin = BooleanField(default=False)

    def set_password(self, password):
        """Establece la contraseña del usuario utilizando bcrypt."""
        logger.info(f"Configurando contraseña para el usuario {self.username}")
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica la contraseña del usuario utilizando bcrypt."""
        logger.info(f"Verificando contraseña para el usuario {self.username}")
        return bcrypt.check_password_hash(self.password, password)

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verifica el token de reseteo de contraseña."""
        logger.debug("Verificando token de reseteo de contraseña")
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
            logger.info(f"Token válido para el usuario ID: {user_id}")
        except Exception as e:
            logger.error(f"Error verificando el token: {e}")
            return None
        return User.objects(id=user_id).first()

    def get_reset_token(self, expires_sec=1800):
        """Genera un token de reseteo de contraseña."""
        logger.debug(f"Generando token de reseteo de contraseña para el usuario {self.username}")
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': str(self.id)})

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Container(Document):
    name = StringField(required=True)
    location = StringField(required=True)
    items = ListField(StringField())
    image_files = ListField(StringField())  # Lista de nombres de archivos de imágenes
    qr_image = StringField()
    user = ReferenceField(User, required=True, reverse_delete_rule='CASCADE')

    def __repr__(self):
        return f"Container('{self.name}', '{self.location}')"