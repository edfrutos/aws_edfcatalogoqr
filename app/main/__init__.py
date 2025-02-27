import mongoengine_patch  # Importar el parche para flask_mongoengine
# ... código existente ...
from flask import Blueprint

main_bp = Blueprint("main", __name__)

from app.main import routes
