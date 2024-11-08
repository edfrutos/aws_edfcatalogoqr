from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, HiddenField, PasswordField, BooleanField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
from app.models import User, Container
from flask_login import current_user

class BaseUserForm(FlaskForm):
    def validate_username(self, username):
        if current_user.is_authenticated and username.data != current_user.username:
            user = User.objects(username=username.data).first()
            if user:
                raise ValidationError('Ese nombre de usuario está siendo usado. Por favor, elige uno diferente.')

    def validate_email(self, email):
        if current_user.is_authenticated and email.data != current_user.email:
            user = User.objects(email=email.data).first()
            if user:
                raise ValidationError('Ese correo electrónico está tomado. Por favor, elige uno diferente.')

class RegistrationForm(BaseUserForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Password', validators=[DataRequired(), EqualTo('password')])
    picture = FileField('Foto de Perfil', validators=[FileAllowed(['jpeg', 'jpg', 'png'])])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    email_or_username = StringField('Email o Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recuérdame')
    submit = SubmitField('Ingresar')

class UpdateAccountForm(BaseUserForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Actualizar Foto de Perfil', validators=[FileAllowed(['jpeg', 'jpg', 'png'])])
    address = StringField('Dirección')
    phone = StringField('Teléfono')
    submit = SubmitField('Actualizar')

class ContainerForm(FlaskForm):
    name = StringField('Nombre del Contenedor', validators=[DataRequired(), Length(min=2, max=50)])
    location = StringField('Ubicación', validators=[DataRequired(), Length(min=2, max=100)])
    items = TextAreaField('Elementos (separados por comas)', validators=[DataRequired()])
    pictures = FileField('Añadir Imágenes', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes')])
    submit = SubmitField('Crear Contenedor')

    def validate_name(self, name):
        if Container.objects(name=name.data).first():
            raise ValidationError('El nombre del contenedor ya está en uso. Por favor, elige un nombre diferente.')

class EditContainerForm(FlaskForm):
    name = StringField('Nombre del Contenedor', validators=[DataRequired(), Length(min=2, max=50)])
    location = StringField('Ubicación', validators=[DataRequired(), Length(min=2, max=100)])
    items = TextAreaField('Elementos (separados por comas)', validators=[DataRequired()])
    pictures = MultipleFileField('Añadir Imágenes', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes')])
    submit = SubmitField('Guardar Cambios')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Recuperación de Contraseña')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Restablecer Contraseña')

class DeleteAccountForm(FlaskForm):
    confirm = BooleanField('Confirmo que quiero eliminar mi cuenta.', validators=[DataRequired()])
    submit = SubmitField('Borrar cuenta')

class ContactForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Mensaje', validators=[DataRequired()])
    submit = SubmitField('Enviar Mensaje')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Nueva contraseña', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')

class UpdateUserForm(BaseUserForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Actualizar Foto de Perfil', validators=[FileAllowed(['jpeg', 'jpg', 'png'])])
    address = StringField('Dirección')
    phone = StringField('Teléfono')
    is_admin = BooleanField('Admin')
    submit = SubmitField('Actualizar Usuario')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.objects(username=username.data).first()
            if user:
                raise ValidationError('Ese nombre de usuario está siendo usado. Por favor, elige uno diferente.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.objects(email=email.data).first()
            if user:
                raise ValidationError('Ese correo electrónico está tomado. Por favor, elige uno diferente.')

class SearchContainerForm(FlaskForm):
    search_query = StringField('Buscar contenedor', validators=[DataRequired()])
    submit = SubmitField('Buscar')

class SearchUserForm(FlaskForm):
    search = StringField('Buscar Usuario (por nombre de usuario o email)', validators=[DataRequired()])
    submit = SubmitField('Buscar')

#Crea un formulario para manejar la eliminación de imágenes.
class DeleteImageForm(FlaskForm):
    delete_image_id = HiddenField()
    submit = SubmitField('Eliminar')