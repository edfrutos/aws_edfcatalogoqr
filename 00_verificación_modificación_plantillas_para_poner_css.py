import os

def ensure_extends_layout(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    if '{% extends "layout.html" %}' not in content:
        content = '{% extends "layout.html" %}\n' + content

    with open(file_path, 'w') as file:
        file.write(content)

def process_templates(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                ensure_extends_layout(os.path.join(root, file))

# Procesar las carpetas templates/ y templates/admin/
process_templates('templates')
process_templates('templates/admin')