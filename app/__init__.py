# app/__init__.py
import os
import ssl
import logging
import certifi
from flask import Flask
from dotenv import load_dotenv
from mongoengine import connect, disconnect, ConnectionFailure
from logging.handlers import RotatingFileHandler
from app.config import Config
from app.extensions import db, bcrypt, login_manager, mail, csrf

# Configuración del certificado SSL para MongoDB
os.environ['SSL_CERT_FILE'] = certifi.where()

# Cargar variables de entorno desde .env
load_dotenv()

def configure_logging(app):
    """Configura el logging para la aplicación Flask."""
    if not app.debug:
        # Crear el directorio de logs si no existe
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # Usar RotatingFileHandler para manejar los logs y evitar que crezcan demasiado
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Establecer el nivel de logging para la aplicación
    app.logger.setLevel(logging.INFO)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Limitar el tamaño de archivos que se pueden subir, ejemplo 16 MB
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Inicializar las extensiones con la aplicación Flask
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Desconectar cualquier conexión existente antes de conectar a la nueva base de datos
    try:
        disconnect(alias='default')
        connect(
            db=app.config['MONGODB_SETTINGS']['db'],
            host=app.config['MONGODB_SETTINGS']['host'],
            tls=True,
            tlsAllowInvalidCertificates=True,
            ssl_cert_reqs=ssl.CERT_NONE
        )
        app.logger.info('Conexión a MongoDB establecida correctamente')
    except ConnectionFailure as e:
        app.logger.error(f'Error al conectar con MongoDB: {e}')
        raise e

    # Configurar el logging
    configure_logging(app)

    # Registrar mensajes de log en la inicialización de la aplicación
    app.logger.info('Aplicación Flask iniciada correctamente')

    # Registrar el Blueprint principal
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Registrar el Blueprint de administración con prefijo /admin
    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app

# Crear la instancia de la aplicación Flask a nivel de módulo
app = create_app()