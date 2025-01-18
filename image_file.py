from pymongo import MongoClient

# Conexión a la base de datos
client = MongoClient(
    "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["app-qr-catalogacion"]
collection = db["containers"]

# Añade el campo image_file a los documentos que no lo tienen
collection.update_many(
    {"image_file": {"$exists": False}}, {"$set": {"image_file": "default.jpg"}}
)
