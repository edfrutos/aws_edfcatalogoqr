import os
import ssl
import logging
from flask import Flask
from dotenv import load_dotenv
from mongoengine import connect, disconnect
from app.config import Config
from app.extensions import db, bcrypt, login_manager, mail, csrf

# Cargar variables de entorno desde .env
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar las extensiones con la aplicación Flask
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Desconectar cualquier conexión existente antes de conectar a la nueva base de datos
    disconnect(alias='default')
    connect(
        db=app.config['MONGODB_SETTINGS']['db'],
        host=app.config['MONGODB_SETTINGS']['host'],
        tls=True,
        tlsAllowInvalidCertificates=True,
        ssl_cert_reqs=ssl.CERT_NONE
    )

    # Configurar el logging
    configure_logging(app)

    app.logger.info('Aplicación iniciada')

    # Registrar el Blueprint principal
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Registrar el Blueprint de administración
    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app

def configure_logging(app):
    """Configura el logging para la aplicación Flask."""
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)