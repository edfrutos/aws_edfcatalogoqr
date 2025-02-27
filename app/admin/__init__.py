import mongoengine_patch  # Importar el parche para flask_mongoengine
# ... código existente ...
from flask import Blueprint

admin = Blueprint("admin", __name__)

from app.admin import routes
