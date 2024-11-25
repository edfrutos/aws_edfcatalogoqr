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
            'logs/routes.log',
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

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email_or_username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        flash('Email o contraseña incorrectos', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)


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

from flask import abort
# Primero las importaciones necesarias
from flask import flash, current_app, render_template, url_for, redirect, request, Blueprint, abort, send_file, session, jsonify
from flask_login import login_user, current_user, logout_user, login_required
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

# Ejemplo de una ruta con el nuevo manejo de errores
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

# Ejemplo de una ruta mejorada con el nuevo sistema de logging
@main.route('/container/<container_id>')
@login_required
@handle_errors
def container_detail(container_id):
    logger.info(f"Accediendo a los detalles del contenedor: {container_id}")
    
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            logger.warning(f"Contenedor no encontrado: {container_id}")
            abort(404)
        
        # Verificar imágenes válidas
        valid_images = verify_container_images(container)
        container.image_files = valid_images
        
        logger.info(f"Contenedor {container_id} cargado exitosamente")
        return render_template('container_detail.html', 
                             container=container,
                             image_size={'width': 200, 'height': 'auto'})
                             
    except Exception as e:
        logger.error(f"Error al cargar el contenedor {container_id}: {e}")
        flash("Error al cargar los detalles del contenedor", "danger")
        return redirect(url_for('main.list_containers'))



import re  # Asegúrate de tener importada esta librería para limpiar el nombre del archivo QR

@main.route('/create_container', methods=['GET', 'POST'])
@login_required
def create_container():
    form = ContainerForm()
    if form.validate_on_submit():
        logger.info("Creación de contenedor iniciada.")
        pictures = form.pictures.data
        picture_files = []

        for picture in pictures:
            if isinstance(picture, FileStorage) and picture.filename != '':
                try:
                    picture_file = save_container_picture(picture)
                    picture_files.append(picture_file)
                except Exception as e:
                    logger.error(f"Error al guardar la imagen: {e}")
                    flash('Error al guardar una de las imágenes.', 'danger')
                    return render_template('create_container.html', form=form)
            else:
                logger.error("El objeto proporcionado no es un archivo válido")
                flash('Uno de los archivos proporcionados no es válido.', 'danger')
                return render_template('create_container.html', form=form)

        # Limpiar el nombre para el código QR
        safe_name = re.sub(r'[^\w\s-]', '', form.name.data).strip().replace(' ', '_')

        # Generar el código QR
        qr_data = f"Contenedor: {form.name.data}\nUbicación: {form.location.data}\nObjetos: {form.items.data}"
        qr_img_path = os.path.join(current_app.root_path, 'static', 'qr_codes', f"{safe_name}.png")

        try:
            qr_img = qrcode.make(qr_data)
            qr_img.save(qr_img_path)
        except Exception as e:
            logger.error(f"Error al guardar el código QR: {e}")
            flash('Error al generar el código QR', 'danger')
            return render_template('create_container.html', form=form)

        # Guardar el contenedor en la base de datos
        container = Container(
            name=form.name.data,
            location=form.location.data,
            items=[item.strip() for item in form.items.data.split(",")],
            image_files=picture_files,
            qr_image=f"{safe_name}.png",
            user=current_user._get_current_object()
        )

        try:
            container.save()
            logger.info(f"Contenedor creado con ID: {container.id}")
            flash('El contenedor se ha creado exitosamente.', 'success')
            return redirect(url_for('main.container_detail', container_id=container.id))
        except NotUniqueError:
            flash('El nombre del contenedor ya está en uso. Por favor, elige un nombre diferente.', 'danger')
            logger.error("El nombre del contenedor ya está en uso.")

    return render_template('create_container.html', form=form)

@main.route("/containers/<container_id>/preview", methods=["GET"])
@login_required
def container_preview(container_id):
    try:
        container = Container.objects.get(id=container_id)
        return render_template('container_preview.html', container=container)
    except Container.DoesNotExist:
        logger.error(f"Contenedor con ID {container_id} no encontrado.")
        abort(404)

@main.route("/containers/<container_id>/download_qr")
@login_required
def download_qr(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)
    qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container.qr_image)
    return send_file(qr_path, as_attachment=True)

@main.route("/download_container/<container_id>")
@login_required
def download_container(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)
    qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container.qr_image)
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True, download_name=container.qr_image)
    else:
        flash('Código QR no encontrado', 'danger')
        return redirect(url_for('main.container_detail', container_id=container_id))

@main.route("/containers", methods=['GET', 'POST'])
@login_required
def list_containers():
    form = SearchContainerForm()
    search_query = request.args.get('search_query', '')
    containers = current_user.get_containers(search_query)
    return render_template('list_containers.html', 
                         title='Mis Contenedores', 
                         containers=containers, 
                         form=form)

@main.route("/containers/<container_id>/edit", methods=["GET", "POST"])
@login_required
def edit_container(container_id):
    logger.debug("Entrando a la función edit_container")
    
    try:
        # Obtener el contenedor
        container = Container.objects(id=container_id).first()
        if not container:
            logger.error(f"Contenedor con id {container_id} no encontrado.")
            abort(404, description="Contenedor no encontrado")

        # Verificar que el usuario actual es el propietario
        if str(container.user.id) != str(current_user.id):
            logger.warning(f"Usuario {current_user.id} intentó editar contenedor {container_id} que no le pertenece")
            abort(403)

        form = EditContainerForm(obj=container)
        delete_form = DeleteImageForm()

        if request.method == "GET":
            # Para GET, mostrar los items como una lista separada por comas
            form.items.data = ", ".join(container.items) if container.items else ""
            return render_template(
                "edit_container.html",
                container=container,
                form=form,
                delete_form=delete_form
            )

        if form.validate_on_submit():
            try:
                # Procesar la lista de objetos, manteniendo mayúsculas y minúsculas
                items_list = [item.strip() for item in form.items.data.split(',') if item.strip()]
                
                # Preparar las actualizaciones
                updates = {
                    "set__name": form.name.data,
                    "set__location": form.location.data,
                    "set__items": items_list
                }

                # Procesar nuevas imágenes
                new_images = []
                if form.pictures.data:
                    for picture in form.pictures.data:
                        if hasattr(picture, 'filename') and picture.filename:
                            try:
                                filename = save_container_picture(picture)
                                if filename:
                                    new_images.append(filename)
                            except Exception as e:
                                logger.error(f"Error guardando imagen {picture.filename}: {e}")
                                continue

                if new_images:
                    updates["push_all__image_files"] = new_images

                # Actualizar el contenedor
                container.update(**updates)
                container.reload()

                flash("Contenedor actualizado correctamente", "success")
                
                # Si es una petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        "success": True,
                        "redirect": url_for("main.container_detail", container_id=container.id)
                    })
                
                # Si es una petición normal, redirigir
                return redirect(url_for("main.container_detail", container_id=container.id))

            except Exception as e:
                logger.error(f"Error actualizando contenedor: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"success": False, "error": str(e)}), 500
                flash("Error al actualizar el contenedor", "danger")
                return redirect(url_for("main.edit_container", container_id=container_id))

        # Si el formulario no es válido
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": False,
                "errors": form.errors
            }), 400

        return render_template(
            "edit_container.html",
            container=container,
            form=form,
            delete_form=delete_form
        )

    except Exception as e:
        logger.error(f"Error inesperado en edit_container: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": str(e)}), 500
        flash("Ha ocurrido un error inesperado", "danger")
        return redirect(url_for("main.list_containers"))

@main.route("/containers/<container_id>/delete_image/<image_name>", methods=["POST"])
@login_required
def delete_container_image(container_id, image_name):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            return jsonify({"success": False, "error": "Contenedor no encontrado"}), 404
            
        # Eliminar archivo físico
        image_path = os.path.join(current_app.root_path, 'static/container_pics', image_name)
        if os.path.exists(image_path):
            os.remove(image_path)
            
        # Actualizar la base de datos
        container.update(pull__image_files=image_name)
        container.reload()
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error eliminando imagen: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@main.route("/containers/<container_id>/print_detail")
@login_required
def print_detail(container_id):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            abort(404)
        
        # Verificar que las imágenes existen
        valid_images = []
        for image in container.image_files:
            image_path = os.path.join(current_app.root_path, 'static', 'container_pics', image)
            if os.path.exists(image_path):
                valid_images.append(image)
            else:
                logger.warning(f"Imagen no encontrada: {image_path}")
        
        # Crear una copia del contenedor con solo las imágenes válidas
        container_data = {
            'name': container.name,
            'location': container.location,
            'items': container.items,
            'image_files': valid_images,
            'qr_image': container.qr_image
        }
        
        return render_template('print_detail.html', 
                             title='Imprimir Detalle',
                             container=container_data)
    except Exception as e:
        logger.error(f"Error en print_detail: {str(e)}")
        flash("Error al preparar la vista de impresión", "danger")
        return redirect(url_for('main.container_detail', container_id=container_id))

@main.route("/containers/<container_id>/delete", methods=["POST"])
@login_required
def delete_container(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)
    container.delete()
    flash("Contenedor eliminado correctamente", 'success')
    return redirect(url_for('main.list_containers'))

@main.route("/print_container/<container_id>")
@login_required
def print_container(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)
    qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container.qr_image)
    if os.path.exists(qr_path):
        return send_file(qr_path, as_attachment=True, download_name=container.qr_image)
    else:
        flash('Código QR no encontrado', 'danger')
        return redirect(url_for('main.container_detail', container_id=container.id))

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

@main.route("/welcome")
@login_required
def welcome():
    return render_template('welcome.html')

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