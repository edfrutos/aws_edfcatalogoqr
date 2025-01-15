# app/logging_config.py
import logging
import os

# Configuración de Logging
if not os.path.exists('logs'):
    os.mkdir('logs')

logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler('logs/app.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
