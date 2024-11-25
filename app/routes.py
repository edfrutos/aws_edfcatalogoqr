# Primero las importaciones necesarias
from flask import Blueprint,flash, current_app, render_template, url_for, redirect, request, abort, send_file, session, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from functools import wraps
import os
import logging
import boto3
from werkzeug.datastructures import FileStorage
from mongoengine.queryset.visitor import Q
from mongoengine.errors import NotUniqueError
from datetime import datetime
import qrcode

# Importaciones locales
from app.models import User, Container
from app.forms import (
    RegistrationForm, LoginForm, UpdateAccountForm, ContainerForm, 
    RequestResetForm, ResetPasswordForm, DeleteAccountForm, ContactForm, 
    ChangePasswordForm, SearchContainerForm, EditContainerForm, DeleteImageForm
)
from app.utils import (
    save_profile_picture, save_container_picture, send_reset_email, 
    save_qr_image, admin_required, normalize_name
)
from app.extensions import db, bcrypt, mail
from flask_mail import Message

# Configuración del Blueprint
main = Blueprint('main', __name__)

# Definir el Blueprint
users_bp = Blueprint('users', __name__)

# Configuración mejorada del logger
def setup_logger():
    logger = logging.getLogger(__name__)
    
    # Evitar duplicación de handlers
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Crear el directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Configurar el RotatingFileHandler
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10,
            encoding='utf-8'
        )
        
        # Configurar el formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Añadir el handler al logger
        logger.addHandler(file_handler)
    
    return logger

# Inicializar el logger
logger = setup_logger()

# Inicializar el cliente de S3
try:
    s3 = boto3.client('s3')
except Exception as e:
    logger.error(f"Error al inicializar el cliente S3: {e}")
    s3 = None
    
# Decorador para manejo de errores
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {f.__name__}: {str(e)}", exc_info=True)
            flash("Ha ocurrido un error inesperado", "danger")
            return redirect(url_for('main.home'))
    return decorated_function

@main.route("/")
@main.route("/home")
@handle_errors
def home():
    try:
        session.pop('show_welcome_modal', None)
        current_year = datetime.now().year
        return render_template('home.html', title='Inicio', current_year=current_year)
    except Exception as e:
        logger.error(f"Error en la ruta home: {e}")
        raise

# Función auxiliar para verificar imágenes
def verify_container_images(container):
    """Verifica y retorna solo las imágenes válidas de un contenedor."""
    valid_images = []
    for image in container.image_files:
        image_path = os.path.join(current_app.root_path, 'static', 'container_pics', image)
        if os.path.exists(image_path):
            valid_images.append(image)
        else:
            logger.warning(f"Imagen no encontrada: {image_path}")
    return valid_images

@main.route('/test')
def test():
    return "La aplicación está funcionando"

@main.route("/about")
def about():
    return render_template('about.html', title='Acerca de')

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.welcome'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            user.image_file = picture_file
        user.save()
        flash('Tu cuenta ha sido creada! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Registro', form=form)

from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app.forms import LoginForm
from app.models import User

users_bp = Blueprint('users', __name__)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.logout_page'))

@main.route("/logout_page")
def logout_page():
    return render_template('logout.html')

@main.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()

    # Procesar el formulario si se están enviando los datos
    if form.validate_on_submit():
        try:
            # Logging del estado antes de la actualización
            current_app.logger.info(f'Iniciando actualización de cuenta para el usuario: {current_user.username}')
            current_app.logger.info(f'Información recibida - Username: {form.username.data}, Email: {form.email.data}, '
                                    f'Address: {form.address.data}, Phone: {form.phone.data}')

            # Manejar la actualización de la foto de perfil
            if form.picture.data:
                current_app.logger.info(f'Actualizando foto de perfil para el usuario: {current_user.username}')
                try:
                    picture_file = save_profile_picture(form.picture.data)
                    current_user.image_file = picture_file
                    current_app.logger.info(f'Foto de perfil actualizada: {picture_file}')
                except Exception as e:
                    current_app.logger.error(f'Error al actualizar la foto de perfil para {current_user.username}: {e}')
                    flash('Error al actualizar la foto de perfil. Intenta nuevamente.', 'danger')
                    return redirect(url_for('users.account'))

            # Verificar si el nombre de usuario ha cambiado
            if form.username.data != current_user.username:
                current_app.logger.info(f'El nombre de usuario ha cambiado de {current_user.username} a {form.username.data}')

            # Actualizar los campos del usuario
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.address = form.address.data
            current_user.phone = form.phone.data

            # Guardar los cambios en la base de datos
            current_user.save()
            current_app.logger.info(f'Cuenta actualizada exitosamente para el usuario: {current_user.username}')

            flash('Tu cuenta ha sido actualizada exitosamente!', 'success')

            # Redirigir para evitar el reenvío del formulario al actualizar
            return redirect(url_for('users.account'))

        except Exception as e:
            # Capturar y registrar errores si ocurre un problema durante la actualización
            current_app.logger.error(f'Error actualizando la cuenta para el usuario {current_user.username}: {e}')
            flash('Ocurrió un error al actualizar la cuenta. Intenta de nuevo.', 'danger')

    # Mostrar los datos actuales si es un GET
    elif request.method == 'GET':
        # Logging de la carga de los datos del usuario
        current_app.logger.info(f'Cargando datos del usuario: {current_user.username}')
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.address.data = current_user.address
        form.phone.data = current_user.phone

    # Obtener la imagen de perfil para mostrarla en la vista
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)

    # Logging de la imagen cargada
    current_app.logger.info(f'Mostrando imagen de perfil para el usuario {current_user.username}: {current_user.image_file}')

    return render_template('account.html', title='Cuenta', image_file=image_file, form=form)

@main.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('Se ha enviado un correo electrónico con instrucciones para restablecer su contraseña.', 'info')
        else:
            flash('No hay ninguna cuenta con ese correo electrónico. Primero debes registrarte.', 'advertencia')
        return redirect(url_for('main.home'))
    return render_template('reset_request.html', form=form)

@main.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash('Ese es un token no válido o caducado', 'advertencia')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()  # Asegúrate de que el usuario se guarda en la base de datos
        flash('¡Su contraseña ha sido actualizada!', 'éxito')
        return redirect(url_for('users.login'))
    return render_template('reset_password.html', form=form)

@main.route("/contacto", methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            msg = Message(
                subject=f"Nuevo mensaje de contacto de {form.name.data}",
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[current_app.config['MAIL_DEFAULT_SENDER']],
                reply_to=form.email.data
            )
            msg.body = f'''
            Nombre: {form.name.data}
            Email: {form.email.data}
            Mensaje:
            {form.message.data}
            '''

            mail.send(msg)
            flash('Tu mensaje ha sido enviado correctamente!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            current_app.logger.error(f"Error enviando email: {str(e)}")
            flash('Hubo un error al enviar el mensaje. Por favor, intenta más tarde.', 'danger')
    return render_template('contacto.html', title='Contacto', form=form)

@main.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            current_user.password = hashed_password
            current_user.save()
            flash('Tu contraseña ha sido actualizada!', 'success')
            return redirect(url_for('users.account'))
        else:
            flash('Contraseña actual incorrecta', 'danger')
    return render_template('change_password.html', title='Cambiar Contraseña', form=form)

@main.route("/delete_account", methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if form.confirm.data:
            user = current_user._get_current_object()
            containers = Container.objects(user=user)
            for container in containers:
                container.delete()
            user.delete()
            flash('Tu cuenta y todos tus contenedores han sido eliminados.', 'success')
            return redirect(url_for('main.home'))
    return render_template('delete_account.html', title='Eliminar Cuenta', form=form)

@main.route("/search_container", methods=['GET', 'POST'])
@login_required
def search_container():
    form = SearchContainerForm()
    search_query = request.args.get('search', '')
    containers = current_user.get_containers(search_query) if search_query else []
    return render_template('search_container.html', 
                         title='Buscar Contenedor', 
                         containers=containers, 
                         form=form)

# Ruta para subir archivos a S3
@main.route('/upload', methods=['POST'])
def upload_file():
    current_app.logger.info('Ruta /upload llamada.')

    if 'file' not in request.files:
        current_app.logger.error('No file part in the request')
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        current_app.logger.error('No selected file')
        return jsonify({"error": "No selected file"}), 400

    try:
        # Subir el archivo a S3 con el prefijo "upload/"
        current_app.logger.info(f'Intentando subir {file.filename} al bucket S3.')
        s3.upload_fileobj(file, 'edfcatalogoqr', f"upload/{file.filename}")
        current_app.logger.info('Archivo subido exitosamente.')
        return jsonify({"message": "File uploaded successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": "File upload failed"}), 500