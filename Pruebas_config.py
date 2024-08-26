import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '72595f0a4ea70881084af49122ebfce37e36c0e1645d26c4c4cd2487b8654c65fd2fd5f9b7ecabfb52a6432afb3d412de0485a324ebf41be70e26f06ea2e2025')
    MONGODB_SETTINGS = {
        'db': 'app-qr-catalogacion',
        'host': os.getenv('MONGO_URI', 'mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority&appName=Cluster0')
    }
    MAIL_SERVER = 'smtp-relay.brevo.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('EMAIL_USER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS')
    WTF_CSRF_ENABLED = True