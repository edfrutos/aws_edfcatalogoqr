from app import create_app
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)

# Crear la aplicación Flask
app = create_app()

with app.app_context():
    secret_key = app.config['SECRET_KEY']
    logging.info(f"SECRET_KEY cargado: {secret_key}")
    print(f"SECRET_KEY cargado: {secret_key}")
