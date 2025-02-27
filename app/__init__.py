from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_mongoengine import MongoEngine
from datetime import datetime
import certifi
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from mongoengine import disconnect
import os
import logging
import mongoengine_patch  # Importar el parche para flask_mongoengine
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    """
    Configura el logger de Flask con un RotatingFileHandler para manejar los logs.

    Args:
        app: Instancia de la aplicación Flask.
    """
    # Crear el directorio de logs si no existe
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Configurar archivo de logs
    log_file = os.path.join(log_dir, "app.log")
    if not app.debug:  # Evitar problemas en modo debug con múltiples procesos
        # Configurar RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Agregar handler al logger de Flask
        if not app.logger.handlers:
            app.logger.addHandler(file_handler)

    # Configuración general del logger de Flask
    app.logger.setLevel(logging.INFO)
    app.logger.info("Logger configurado correctamente")


# Configuración adicional para logging independiente (opcional)
logger = logging.getLogger("app")
if not logger.handlers:
    handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)
logger.info("Logger independiente configurado correctamente")

# Establece la ruta del certificado SSL para evitar errores de verificación de MongoDB
os.environ["SSL_CERT_FILE"] = certifi.where()

# Cargar variables de entorno
load_dotenv()

# Inicialización de extensiones
db = MongoEngine()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
moment = Moment()

# Configuración del login
login_manager.login_view = "users.login"
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"


def create_app():
    # Desconectar cualquier conexión existente antes de crear una nueva
    disconnect()

    app = Flask(__name__)

    # Configuración básica
    secret_key = os.environ.get("SECRET_KEY", "default-secret-key")
    if not isinstance(secret_key, (str, bytes)):
        raise ValueError("SECRET_KEY debe ser una cadena o bytes.")
    app.config["SECRET_KEY"] = (
        secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    )

    app.config["MONGODB_SETTINGS"] = {
        "host": os.environ.get("MONGO_URI", "mongodb://localhost:27017/edfcatalogoqr"),
        "connect": False,  # MongoEngine se conectará automáticamente a través de init_app
    }

    # Configuración de AWS S3
    app.config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    app.config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    app.config["AWS_BUCKET_NAME"] = os.environ.get("AWS_BUCKET_NAME")

    # Configuración de correo
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = (
        os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    )
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

    # Validación de configuraciones críticas
    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        app.logger.warning(
            "MAIL_USERNAME o MAIL_PASSWORD no están configurados correctamente."
        )

    # Inicialización de extensiones con la app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    # Configuración de logging
    if not app.debug:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Aplicación Flask iniciada correctamente")

    # Registro de blueprints
    from app.main.routes import main_bp
    from app.users.routes import users_bp
    from app.admin.routes import admin_bp
    from app.errors.handlers import errors

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(errors)

    # Configuración de contexto global
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.utcnow().year}

    # Inicialización de cliente S3
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"],
        )
        app.config["S3_CLIENT"] = s3_client
    except ClientError as e:
        app.logger.error(f"Error al inicializar el cliente S3: {str(e)}")

    # Manejo de errores HTTP
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500

    return app


# Configuración del cargador de usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        from app.models import User

        user = User.objects(id=user_id).first()
        if user:
            logging.info(f"Usuario cargado: {user.username}")
        else:
            logging.warning("No se encontró el usuario en la base de datos.")
        return user
    except Exception as e:
        logging.error(f"Error al cargar el usuario: {str(e)}")
        return None
