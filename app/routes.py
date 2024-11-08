from flask import flash, current_app, render_template, url_for, redirect, request, Blueprint, abort, send_file, session, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app.models import User, Container
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, ContainerForm, RequestResetForm, ResetPasswordForm, DeleteAccountForm, ContactForm, ChangePasswordForm, SearchContainerForm, EditContainerForm, DeleteImageForm
from app.utils import save_profile_picture, save_container_picture, send_reset_email, save_qr_image, admin_required, normalize_name
import os
import logging
import boto3
from werkzeug.datastructures import FileStorage
from app.extensions import db, bcrypt, mail
from flask_mail import Message
import qrcode
from mongoengine.queryset.visitor import Q
from mongoengine.errors import NotUniqueError
from datetime import datetime


main = Blueprint('main', __name__)

# Inicializar el cliente de boto3 para S3
s3 = boto3.client('s3')

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('logs/app.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@main.route("/")
@main.route("/home")
def home():
    session.pop('show_welcome_modal', None)  # Limpiar la sesión de modal de bienvenida
    current_year = datetime.now().year
    return render_template('home.html', title='Inicio', current_year=current_year)

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
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Registro', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email_or_username.data).first() or User.objects(username=form.email_or_username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            session['show_welcome_modal'] = True
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.welcome'))
        else:
            flash('Inicio de sesión no exitoso. Por favor verifica tu correo/usuario y contraseña.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.logout_page'))

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
                    return redirect(url_for('main.account'))

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
            return redirect(url_for('main.account'))

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
        return redirect(url_for('main.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()  # Asegúrate de que el usuario se guarda en la base de datos
        flash('¡Su contraseña ha sido actualizada!', 'éxito')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', form=form)

@main.route("/contacto", methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(
            subject=f"{form.name.data} ha enviado un mensaje",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=['admin@efjdefrutos.com'],
            reply_to=form.email.data  # Dirección del usuario como respuesta
        )
        msg.body = f'''
        Nombre: {form.name.data}
        Email de contacto: {form.email.data}
        Mensaje: {form.message.data}
        '''
        
        with current_app.app_context():
            mail.send(msg)
        
        flash('Tu mensaje ha sido enviado!', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('contacto.html', title='Contacto', form=form)

from flask import abort
@main.route('/container/<container_id>')
@login_required
def container_detail(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)

    # Convertir `items` a una sola línea de texto con comas
    items_text = ", ".join([item.strip() for item in container.items]) if container.items else ""

    # Definir el tamaño de la imagen
    image_size = {'width': 200, 'height': 'auto'}

    return render_template(
        'container_detail.html',
        container=container,
        items_text=items_text,
        image_size=image_size
    )

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
    containers = Container.objects(user=current_user._get_current_object())
    if search_query:
        containers = containers.filter(
            Q(name__icontains=search_query) | Q(location__icontains=search_query) | Q(items__icontains=search_query)
        )
    return render_template('list_containers.html', title='Mis Contenedores', containers=containers, form=form)

@main.route("/containers/<container_id>/edit", methods=["GET", "POST"])
@login_required
def edit_container(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404, description="Contenedor no encontrado")

    # Verificar que el usuario actual es el propietario del contenedor
    if str(container.user.id) != str(current_user.id):
        abort(403)

    # Crear el formulario de edición y el formulario de eliminación
    form = EditContainerForm(obj=container)
    delete_form = DeleteImageForm()  # Definir delete_form aquí

    if request.method == "GET":
        # Mostrar los objetos como una cadena separada por comas
        form.items.data = ", ".join(container.items) if container.items else ""

    if form.validate_on_submit():
        # Convertir `items` en una lista y asignarla al contenedor
        items_list = [item.strip() for item in form.items.data.split(",") if item.strip()]
        container.items = items_list

        # Procesar y agregar nuevas imágenes
        new_images = []
        if form.pictures.data:
            for picture in form.pictures.data:
                if picture.filename != '':
                    filename = save_container_picture(picture)
                    new_images.append(filename)
        if new_images:
            container.image_files.extend(new_images)

        # Guardar el contenedor con los cambios
        container.save()
        flash("Contenedor actualizado correctamente", "success")
        return redirect(url_for("main.container_detail", container_id=container.id))

    return render_template(
        "edit_container.html",
        container=container,
        form=form,
        delete_form=delete_form  # Pasar delete_form al render_template
    )

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
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)
    return render_template('print_detail.html', title='Imprimir Detalle', container=container)

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
            return redirect(url_for('main.account'))
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
    if search_query:
        containers = Container.objects(
            (Q(name__icontains=search_query) | Q(location__icontains=search_query) | Q(items__icontains=search_query)) & Q(user=current_user._get_current_object())
        )
    else:
        containers = Container.objects(user=current_user._get_current_object())
    return render_template('search_container.html', title='Buscar Contenedor', containers=containers, form=form)

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