from pymongo import MongoClient

# Conexión a la base de datos
client = MongoClient(
    "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["app-qr-catalogacion"]
collection = db["containers"]

# Muestra los primeros 10 documentos en la colección
for container in collection.find().limit(10):
    print(container)

# Muestra sólo el campo image_file para los primeros 10 documentos
for container in collection.find({}, {"image_file": 1}):
    print(container)
