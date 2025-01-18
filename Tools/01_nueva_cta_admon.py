# Crear una nueva cuenta de administrador
from app.models import User

admin = User(username="administrador", email="admin@example.com")
admin.set_password("34Maf15si")
admin.is_admin = True
admin.save()
