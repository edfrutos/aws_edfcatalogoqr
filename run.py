from flask import Flask
from app import create_app

app = create_app()

if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
    except OSError as e:
        print(f"Error al iniciar la aplicación: {e}")
        print("Intente usar un puerto diferente o asegúrese de que no haya otras instancias ejecutándose")