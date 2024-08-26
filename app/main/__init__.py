from flask import Blueprint

main = Blueprint('main', __name__)

from app.admin import routes  # Importa routes al final