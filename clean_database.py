from app import create_app
from app.models import Container

app = create_app()
app.app_context().push()

# Eliminar el campo `date_posted` de todos los documentos `Container`
for container in Container.objects():
    if 'date_posted' in container:
        container.unset('date_posted')
        container.save()

print("Campo 'date_posted' eliminado de todos los documentos Container.")