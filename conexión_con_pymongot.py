from pymongo import MongoClient

# Cambia esto por tu URI real
uri = "pythonmongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)  # 5 segundos de timeout
    db = client.get_database()
    print("Conexión exitosa a MongoDB")
except Exception as e:
    print(f"Error de conexión: {e}")
