from flask import Flask
from app import create_app
from logging.handlers import RotatingFileHandler
import os

# Crear la aplicación Flask
app = create_app()


def main():
    """
    Punto de entrada principal para ejecutar la aplicación Flask.
    Maneja posibles errores al iniciar y ajusta la configuración del logger si está en modo debug.
    """
    try:
        # Ejecutar la aplicación
        app.run(
            host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
            port=int(os.getenv("FLASK_RUN_PORT", 5001)),
            debug=True)
    except OSError as e:
        print(f"Error al iniciar la aplicación: {e}")
        print(
            "Intente usar un puerto diferente o asegúrese de que no haya otras instancias ejecutándose"
        )

    # Ajustar logger en modo debug para evitar conflictos
    if app.debug:
        disable_log_rollover()


def disable_log_rollover():
    """
    Deshabilita el rollover del RotatingFileHandler en modo debug.
    Esto previene errores cuando Flask recarga automáticamente la aplicación.
    """
    for handler in app.logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.doRollover = lambda: None
            app.logger.info(
                "Rollover deshabilitado para RotatingFileHandler en modo debug"
            )


if __name__ == "__main__":
    main()
