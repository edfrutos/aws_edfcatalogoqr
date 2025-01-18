import mongoengine as db

DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"

try:
    db.connect(host=DB_URI)
    print("Conexión exitosa a MongoDB")
except db.connection.ConnectionError as e:
    print(f"Error de conexión: {e}")
