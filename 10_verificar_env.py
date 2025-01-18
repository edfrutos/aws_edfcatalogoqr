import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Verificar variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

print(f"MONGO_URI: {MONGO_URI}")
print(f"SECRET_KEY: {SECRET_KEY}")
print(f"EMAIL_USER: {EMAIL_USER}")
print(f"EMAIL_PASS: {EMAIL_PASS}")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está definido en el archivo .env")
