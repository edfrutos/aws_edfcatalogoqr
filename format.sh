#!/usr/bin/env bash

# Salir inmediatamente si ocurre un error
set -e

# Función para formatear archivos JavaScript, CSS y HTML estándar con Prettier
format_with_prettier() {
  echo "Formateando archivos estándar con Prettier..."
  npx prettier --write "**/*.{js,css,html}" || {
    echo "Error al formatear archivos con Prettier"
    exit 1
  }
}

# Función para formatear plantillas Django con djlint
format_with_djlint() {
  echo "Formateando plantillas Django con djlint..."
  djlint --reformat "**/*.html" || {
    echo "Error al formatear plantillas con djlint"
    exit 1
  }
}

# Ejecutar funciones
format_with_prettier
format_with_djlint

echo "Formateo completado con éxito."
