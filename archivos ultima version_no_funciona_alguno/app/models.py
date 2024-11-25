import logging
from datetime import datetime
from itsdangerous import TimedSerializer as Serializer
from flask_login import UserMixin
from flask import current_app
from mongoengine import (
    Document, 
    StringField, 
    ListField, 
    BooleanField, 
    ReferenceField, 
    DateTimeField,
    CASCADE,
    connect, 
    disconnect,
    Q
)
from app.extensions import login_manager, bcrypt, db

# Configuración de Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler('logs/app.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Configuración de la base de datos
DB_URI = "mongodb+srv://edfrutos:8TrFzqaQxiXkyxFy@cluster0.i5wdlhj.mongodb.net/app-qr-catalogacion?retryWrites=true&w=majority"

def init_db():
    """Inicializa la conexión a la base de datos."""
    try:
        disconnect()
        logger.info("Desconexión exitosa de la base de datos anterior.")
        connect(host=DB_URI)
        logger.info("Conectado exitosamente a la base de datos.")
    except Exception as e:
        logger.error(f"Error en la conexión a la base de datos: {e}")
        raise

init_db()

@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario por ID para Flask-Login."""
    try:
        logger.debug(f"Cargando usuario con ID: {user_id}")
        return User.objects(id=user_id).first()
    except Exception as e:
        logger.error(f"Error al cargar usuario: {e}")
        return None

class User(Document, UserMixin):
    """Modelo de Usuario."""
    username = StringField(max_length=50, unique=True, required=True)
    email = StringField(max_length=50, unique=True, required=True)
    password = StringField(required=True)
    image_file = StringField(default='default.jpg')
    address = StringField()
    phone = StringField()
    is_admin = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()

    meta = {
        'collection': 'users',
        'indexes': ['username', 'email'],
        'ordering': ['-created_at']
    }

    def set_password(self, password):
        """Establece la contraseña del usuario utilizando bcrypt."""
        try:
            logger.info(f"Configurando contraseña para el usuario {self.username}")
            self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        except Exception as e:
            logger.error(f"Error al establecer contraseña: {e}")
            raise

    def check_password(self, password):
        """Verifica la contraseña del usuario utilizando bcrypt."""
        try:
            logger.debug(f"Verificando contraseña para el usuario {self.username}")
            return bcrypt.check_password_hash(self.password, password)
        except Exception as e:
            logger.error(f"Error al verificar contraseña: {e}")
            return False

    def get_reset_token(self, expires_sec=1800):
        """Genera un token de reseteo de contraseña."""
        try:
            logger.debug(f"Generando token de reseteo para {self.username}")
            s = Serializer(current_app.config['SECRET_KEY'])
            return s.dumps(
                {'user_id': str(self.id)}, 
                salt=current_app.config['SECURITY_PASSWORD_SALT']
            )
        except Exception as e:
            logger.error(f"Error al generar token: {e}")
            raise
    def get_containers(self, search_query=None):
        """
        Obtiene todos los contenedores del usuario con opción de búsqueda.
        Args:
            search_query (str, optional): Término de búsqueda para filtrar contenedores.
        Returns:
            Lista de contenedores que coinciden con los criterios.
        """
        try:
            query = Container.objects(user=self)
            if search_query:
                query = query.filter(
                    Q(name__icontains=search_query) |
                    Q(location__icontains=search_query) |
                    Q(items__icontains=search_query)
                )
            logger.info(f"Contenedores recuperados para usuario {self.username}")
            return query
        except Exception as e:
            logger.error(f"Error al obtener contenedores para {self.username}: {e}")
            return []

    def get_containers_count(self):
        """
        Obtiene el número total de contenedores del usuario.
        Returns:
            int: Número de contenedores.
        """
        try:
            count = Container.objects(user=self).count()
            logger.debug(f"Conteo de contenedores para {self.username}: {count}")
            return count
        except Exception as e:
            logger.error(f"Error al contar contenedores para {self.username}: {e}")
            return 0

    def get_recent_containers(self, limit=5):
        """
        Obtiene los contenedores más recientes del usuario.
        Args:
            limit (int): Número máximo de contenedores a retornar.
        Returns:
            Lista de contenedores más recientes.
        """
        try:
            containers = Container.objects(user=self).order_by('-id').limit(limit)
            logger.debug(f"Contenedores recientes recuperados para {self.username}")
            return containers
        except Exception as e:
            logger.error(f"Error al obtener contenedores recientes para {self.username}: {e}")
            return []


    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verifica el token de reseteo de contraseña."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(
                token, 
                salt=current_app.config['SECURITY_PASSWORD_SALT'], 
                max_age=expires_sec
            )['user_id']
            logger.info(f"Token válido para usuario ID: {user_id}")
            return User.objects(id=user_id).first()
        except Exception as e:
            logger.error(f"Error al verificar token: {e}")
            return None

    def update_last_login(self):
        """Actualiza la fecha del último login."""
        self.last_login = datetime.utcnow()
        self.save()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Container(Document):
    """Modelo de Contenedor."""
    name = StringField(required=True)
    location = StringField(required=True)
    items = ListField(StringField())
    image_files = ListField(StringField())
    qr_image = StringField()
    user = ReferenceField('User', reverse_delete_rule=CASCADE, required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'containers',
        'indexes': ['name', 'user'],
        'ordering': ['-created_at']
    }

    def save(self, *args, **kwargs):
        """Sobrescribe el método save para actualizar updated_at."""
        self.updated_at = datetime.utcnow()
        return super(Container, self).save(*args, **kwargs)

    def remove_image(self, image_name):
        """Elimina una imagen del contenedor."""
        try:
            if image_name in self.image_files:
                self.image_files.remove(image_name)
                self.save()
                logger.info(f"Imagen {image_name} eliminada del contenedor {self.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar imagen {image_name}: {e}")
            return False

    def add_image(self, image_name):
        """Añade una nueva imagen al contenedor."""
        try:
            if image_name not in self.image_files:
                self.image_files.append(image_name)
                self.save()
                logger.info(f"Imagen {image_name} añadida al contenedor {self.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al añadir imagen {image_name}: {e}")
            return False

    def __repr__(self):
        return f"Container('{self.name}', '{self.location}')"

    @classmethod
    def get_by_location(cls, location, user=None):
        """
        Obtiene contenedores por ubicación.
        Args:
            location (str): Ubicación a buscar.
            user (User, optional): Usuario para filtrar contenedores.
        Returns:
            Lista de contenedores en esa ubicación.
        """
        try:
            query = cls.objects(location__icontains=location)
            if user:
                query = query.filter(user=user)
            logger.debug(f"Búsqueda por ubicación: {location}")
            return query
        except Exception as e:
            logger.error(f"Error en búsqueda por ubicación {location}: {e}")
            return []

    @classmethod
    def search(cls, query, user=None):
        """
        Búsqueda general en contenedores.
        Args:
            query (str): Término de búsqueda.
            user (User, optional): Usuario para filtrar contenedores.
        Returns:
            Lista de contenedores que coinciden con la búsqueda.
        """
        try:
            base_query = cls.objects(
                Q(name__icontains=query) |
                Q(location__icontains=query) |
                Q(items__icontains=query)
            )
            if user:
                base_query = base_query.filter(user=user)
            logger.debug(f"Búsqueda general con término: {query}")
            return base_query
        except Exception as e:
            logger.error(f"Error en búsqueda general: {e}")
            return []

    def add_item(self, item):
        """
        Añade un ítem al contenedor.
        Args:
            item (str): Ítem a añadir.
        Returns:
            bool: True si se añadió correctamente.
        """
        try:
            if item not in self.items:
                self.items.append(item)
                self.save()
                logger.info(f"Ítem '{item}' añadido al contenedor {self.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al añadir ítem al contenedor {self.name}: {e}")
            return False

    def remove_item(self, item):
        """
        Elimina un ítem del contenedor.
        Args:
            item (str): Ítem a eliminar.
        Returns:
            bool: True si se eliminó correctamente.
        """
        try:
            if item in self.items:
                self.items.remove(item)
                self.save()
                logger.info(f"Ítem '{item}' eliminado del contenedor {self.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar ítem del contenedor {self.name}: {e}")
            return False

    def update_location(self, new_location):
        """
        Actualiza la ubicación del contenedor.
        Args:
            new_location (str): Nueva ubicación.
        Returns:
            bool: True si se actualizó correctamente.
        """
        try:
            self.location = new_location
            self.save()
            logger.info(f"Ubicación actualizada para contenedor {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar ubicación del contenedor {self.name}: {e}")
            return False
