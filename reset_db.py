# Para usar el script:

# Para reset normal (solo índices):
#  python3 reset_db.py

# Para reset completo (¡elimina todos los datos!):
#  python3 reset_db.py --hard


from mongoengine import connect, disconnect
from pymongo import MongoClient
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

def reset_database():
    # Desconectar cualquier conexión existente
    disconnect()
    
    # Obtener URI de MongoDB desde variables de entorno
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI no está definida en las variables de entorno")
        sys.exit(1)
    
    # Conectar a MongoDB
    client = MongoClient(mongo_uri)
    
    try:
        # Obtener el nombre de la base de datos desde la URI
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        
        # Eliminar todos los índices de la colección containers
        print(f"Eliminando índices de la base de datos {db_name}...")
        db.containers.drop_indexes()
        print("Índices eliminados correctamente")
        
        # Reconectar con mongoengine
        connect(host=mongo_uri)
        
        # Importar el modelo Container y recrear índices
        from app.models import Container
        Container.ensure_indexes()
        print("Índices recreados correctamente")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        client.close()

def hard_reset_database():
    """¡ADVERTENCIA! Esta función eliminará todos los datos de la base de datos."""
    disconnect()
    
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI no está definida en las variables de entorno")
        sys.exit(1)
    
    client = MongoClient(mongo_uri)
    
    try:
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        
        # Solicitar confirmación
        confirm = input(f"¿Estás seguro de que quieres eliminar TODA la base de datos '{db_name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Operación cancelada")
            return
        
        # Eliminar la base de datos
        client.drop_database(db_name)
        print(f"Base de datos {db_name} eliminada correctamente")
        
        # Reconectar y recrear índices
        connect(host=mongo_uri)
        from app.models import Container
        Container.ensure_indexes()
        print("Índices recreados correctamente")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Herramienta de reset de base de datos')
    parser.add_argument('--hard', action='store_true', 
                       help='Realizar un reset completo (elimina todos los datos)')
    
    args = parser.parse_args()
    
    if args.hard:
        hard_reset_database()
    else:
        reset_database()
