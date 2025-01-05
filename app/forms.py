from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, FileField, SubmitField, HiddenField,
    PasswordField, BooleanField, MultipleFileField
)
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError,
    Regexp, Optional
)
from flask_wtf.file import FileAllowed, FileSize
from app.models import User, Container
from flask_login import current_user

# Constantes para validaciones
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png']
USERNAME_REGEX = '^[a-zA-Z0-9_.-]+$'
PHONE_REGEX = r'^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$'

class BaseUserForm(FlaskForm):
    """Clase base para formularios de usuario con validaciones comunes."""
    
    def validate_username(self, username):
        if current_user.is_authenticated and username.data != current_user.username:
            user = User.objects(username=username.data).first()
            if user:
                raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')

    def validate_email(self, email):
        if current_user.is_authenticated and email.data != current_user.email:
            user = User.objects(email=email.data).first()
            if user:
                raise ValidationError('Este correo electrónico ya está registrado. Por favor, usa otro.')

class RegistrationForm(BaseUserForm):
    """Formulario de registro de usuario."""
    username = StringField('Nombre de usuario', validators=[
        DataRequired(),
        Length(min=2, max=20),
        Regexp(USERNAME_REGEX, message="El nombre de usuario solo puede contener letras, números, guiones y puntos.")
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Por favor, introduce un email válido.")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres.")
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    picture = FileField('Foto de Perfil', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, 'Solo se permiten imágenes.'),
        FileSize(max_size=MAX_FILE_SIZE)
    ])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""
    email_or_username = StringField('Email o Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Ingresar')

class UpdateAccountForm(BaseUserForm):
    """Formulario de actualización de cuenta."""
    username = StringField('Nombre de Usuario', validators=[
        DataRequired(),
        Length(min=2, max=20),
        Regexp(USERNAME_REGEX, message="El nombre de usuario solo puede contener letras, números, guiones y puntos.")
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Por favor, introduce un email válido.")
    ])
    picture = FileField('Actualizar Foto de Perfil', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, 'Solo se permiten imágenes.'),
        FileSize(max_size=MAX_FILE_SIZE)
    ])
    address = StringField('Dirección', validators=[Optional(), Length(max=200)])
    phone = StringField('Teléfono', validators=[
        Optional(),
        Regexp(PHONE_REGEX, message="Por favor, introduce un número de teléfono válido.")
    ])
    submit = SubmitField('Actualizar')

class ContainerForm(FlaskForm):
    """Formulario para crear contenedores."""
    name = StringField('Nombre del Contenedor', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    location = StringField('Ubicación', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    items = TextAreaField('Elementos (separados por comas)', validators=[
        DataRequired(),
        Length(max=1000)
    ])
    pictures = MultipleFileField('Añadir Imágenes', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, 'Solo se permiten imágenes.'),
        FileSize(max_size=MAX_FILE_SIZE)
    ])
    submit = SubmitField('Crear Contenedor')

    def validate_name(self, name):
        container = Container.objects(name=name.data, user=current_user.id).first()
        if container:
            raise ValidationError('Ya tienes un contenedor con este nombre. Por favor, elige otro.')

class EditContainerForm(FlaskForm):
    """Formulario para editar contenedores."""
    name = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=2, max=50, message="El nombre debe tener entre 2 y 50 caracteres.")
    ])
    location = StringField('Ubicación', validators=[
        DataRequired(),
        Length(min=2, max=100, message="La ubicación debe tener entre 2 y 100 caracteres.")
    ])
    items = TextAreaField('Objetos', validators=[
        Optional(),
        Length(max=1000, message="La lista de objetos no puede exceder los 1000 caracteres.")
    ])
    pictures = MultipleFileField('Añadir Imágenes', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, 'Solo se permiten imágenes (jpg, jpeg, png).'),
        FileSize(max_size=MAX_FILE_SIZE, message="El tamaño máximo por imagen es 5MB.")
    ])
    submit = SubmitField('Guardar Cambios')

    def __init__(self, original_container=None, *args, **kwargs):
        """
        Inicializa el formulario con el contenedor original para validaciones.
        """
        super(EditContainerForm, self).__init__(*args, **kwargs)
        self.original_container = original_container

    def validate_name(self, field):
        """
        Valida que el nombre del contenedor no esté duplicado para el usuario actual.
        """
        if self.original_container and field.data != self.original_container.name:
            container = Container.objects(
                name=field.data,
                user=current_user.id,
                id__ne=self.original_container.id
            ).first()
            
            if container:
                raise ValidationError('Ya tienes un contenedor con este nombre. Por favor, elige otro.')

class RequestResetForm(FlaskForm):
    """Formulario para solicitar restablecimiento de contraseña."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Por favor, introduce un email válido.")
    ])
    submit = SubmitField('Solicitar Restablecimiento')

    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if not user:
            raise ValidationError('No existe una cuenta con ese email.')

class ResetPasswordForm(FlaskForm):
    """Formulario para restablecer contraseña."""
    password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(),
        Length(min=8, message="La contraseña debe tener al menos 8 caracteres.")
    ])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    submit = SubmitField('Restablecer Contraseña')

class DeleteAccountForm(FlaskForm):
    """Formulario para eliminar cuenta."""
    confirm = BooleanField('Confirmo que quiero eliminar mi cuenta.', validators=[
        DataRequired(message="Debes confirmar que deseas eliminar tu cuenta.")
    ])
    submit = SubmitField('Eliminar Cuenta')

class ContactForm(FlaskForm):
    """Formulario de contacto."""
    name = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Por favor, introduce un email válido.")
    ])
    message = TextAreaField('Mensaje', validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    submit = SubmitField('Enviar Mensaje')

class SearchForm(FlaskForm):
    """Clase base para formularios de búsqueda."""
    search_query = StringField('Buscar', validators=[DataRequired()])
    submit = SubmitField('Buscar')

class SearchContainerForm(SearchForm):
    """Formulario para buscar contenedores."""
    pass

class SearchUserForm(SearchForm):
    """Formulario para buscar usuarios."""
    search_query = StringField('Buscar Usuario (por nombre de usuario o email)', validators=[DataRequired()])
    submit = SubmitField('Buscar')

class DeleteImageForm(FlaskForm):
    """Formulario para eliminar imágenes."""
    image_id = HiddenField('ID de imagen', validators=[DataRequired()])
    submit = SubmitField('Eliminar')

class ChangePasswordForm(FlaskForm):
    """Formulario para cambiar la contraseña."""
    current_password = PasswordField('Contraseña actual', validators=[
        DataRequired(message="Por favor, introduce tu contraseña actual.")
    ])
    new_password = PasswordField('Nueva contraseña', validators=[
        DataRequired(),
        Length(min=8, message="La nueva contraseña debe tener al menos 8 caracteres.")
    ])
    confirm_password = PasswordField('Confirmar nueva contraseña', validators=[
        DataRequired(),
        EqualTo('new_password', message='Las contraseñas deben coincidir.')
    ])
    submit = SubmitField('Cambiar Contraseña')

    def validate_new_password(self, new_password):
        if new_password.data == self.current_password.data:
            raise ValidationError('La nueva contraseña debe ser diferente a la actual.')

class UpdateUserForm(BaseUserForm):
    """Formulario para actualizar usuarios (admin)."""
    username = StringField('Nombre de usuario', validators=[
        DataRequired(),
        Length(min=2, max=20),
        Regexp(USERNAME_REGEX, message="El nombre de usuario solo puede contener letras, números, guiones y puntos.")
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Por favor, introduce un email válido.")
    ])
    picture = FileField('Actualizar Foto de Perfil', validators=[
        Optional(),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, 'Solo se permiten imágenes.'),
        FileSize(max_size=MAX_FILE_SIZE)
    ])
    address = StringField('Dirección', validators=[Optional(), Length(max=200)])
    phone = StringField('Teléfono', validators=[
        Optional(),
        Regexp(PHONE_REGEX, message="Por favor, introduce un número de teléfono válido.")
    ])
    is_admin = BooleanField('Administrador')
    submit = SubmitField('Actualizar Usuario')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.objects(username=username.data).first()
            if user:
                raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.objects(email=email.data).first()
            if user:
                raise ValidationError('Este correo electrónico ya está registrado. Por favor, usa otro.')
