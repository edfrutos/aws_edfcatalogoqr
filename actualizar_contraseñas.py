from werkzeug.security import generate_password_hash
from pymongo import MongoClient

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['config']
users = db['users']

# Actualizar contraseñas
for user in users.find():
    hashed_password = generate_password_hash(user['password'])
    users.update_one({'_id': user['_id']}, {'$set': {'password': hashed_password}})

print("Contraseñas actualizadas correctamente.")