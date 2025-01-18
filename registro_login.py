import logging
from datetime import datetime
from itsdangerous import TimedSerializer as Serializer
from flask_login import UserMixin
from flask import current_app
from mongoengine import (
    Document,
    StringField,
    ListField,
    BooleanField,
    ReferenceField,
    DateTimeField,
    CASCADE,
)
from app.extensions import login_manager, bcrypt

# Configuración de Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler("logs/app.log")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario por ID para Flask-Login."""
    try:
        logger.debug(f"Cargando usuario con ID: {user_id}")
        return User.objects(id=user_id).first()
    except Exception as e:
        logger.error(f"Error al cargar usuario: {e}")
        return None


class User(Document, UserMixin):
    """Modelo de Usuario."""

    username = StringField(max_length=50, unique=True, required=True)
    email = StringField(max_length=50, unique=True, required=True)
    password = StringField(required=True)
    image_file = StringField(default="default.jpg")
    image_files = StringField(default="default.jpg")
    address = StringField()
    phone = StringField()
    is_admin = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()

    meta = {
        "collection": "users",
        "indexes": ["username", "email"],
        "ordering": ["-created_at"],
    }

    def set_password(self, password):
        """Establece la contraseña del usuario utilizando bcrypt."""
        try:
            logger.info(f"Configurando contraseña para el usuario {self.username}")
            self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        except Exception as e:
            logger.error(f"Error al establecer contraseña: {e}")
            raise

    def check_password(self, password):
        """Verifica la contraseña del usuario utilizando bcrypt."""
        try:
            logger.debug(f"Verificando contraseña para el usuario {self.username}")
            return bcrypt.check_password_hash(self.password, password)
        except Exception as e:
            logger.error(f"Error al verificar contraseña: {e}")
            return False

    def get_reset_token(self, expires_sec=1800):
        """Genera un token de reseteo de contraseña."""
        try:
            logger.debug(f"Generando token de reseteo para {self.username}")
            salt = current_app.config.get("SECURITY_PASSWORD_SALT")
            if not salt:
                raise ValueError("SECURITY_PASSWORD_SALT no está definido")
            s = Serializer(current_app.config["SECRET_KEY"])
            return s.dumps({"user_id": str(self.id)}, salt=salt)
        except KeyError as e:
            logger.error(f"Error al generar token: {e}")
            raise
        except Exception as e:
            logger.error(f"Error al generar token: {e}")
            raise

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verifica el token de reseteo de contraseña."""
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(
                token,
                salt=current_app.config["SECURITY_PASSWORD_SALT"],
                max_age=expires_sec,
            )["user_id"]
            logger.info(f"Token válido para usuario ID: {user_id}")
            return User.objects(id=user_id).first()
        except Exception as e:
            logger.error(f"Error al verificar token: {e}")
            return None

    def update_last_login(self):
        """Actualiza la fecha del último login."""
        self.last_login = datetime.utcnow()
        self.save()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Container(Document):
    """Modelo de Contenedor."""

    name = StringField(required=True)
    location = StringField(required=True)
    items = ListField(StringField())
    image_files = ListField(StringField())
    qr_image = StringField()
    user = ReferenceField("User", required=True, reverse_delete_rule=CASCADE)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    is_deleted = BooleanField(
        default=False
    )  # Campo para marcar contenedores eliminados

    meta = {
        "indexes": [{"fields": ["name"], "unique": True}],
        "ordering": ["-created_at"],
    }

    def __repr__(self):
        return f"Container('{self.name}', '{self.location}')"
