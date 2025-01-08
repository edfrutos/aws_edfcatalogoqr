from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_required
from app.forms import UpdateUserForm, SearchUserForm, SearchContainerForm, ContainerForm, DeleteAccountForm
from app.models import User, Container
from app.utils import admin_required, save_profile_picture, save_container_picture
from werkzeug.datastructures import FileStorage
from mongoengine.queryset.visitor import Q
import unidecode
import logging
import mongoengine
from pathlib import Path

admin_bp = Blueprint('admin', __name__)

# Configuración del logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Asegurar que el directorio de logs existe
Path('logs').mkdir(exist_ok=True)

# Configurar RotatingFileHandler para mejor manejo de logs
handler = logging.handlers.RotatingFileHandler(
    'logs/app.log',
    maxBytes=1024 * 1024,  # 1MB
    backupCount=5,
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@admin_bp.route("/admin/users", methods=['GET', 'POST'])
@login_required
@admin_required
def list_users():
    form = SearchUserForm()
    users = User.objects.all()
    return render_template('admin/list_users.html', title='Listar Usuarios', users=users, form=form)

@admin_bp.route("/admin/user/<user_id>/edit", methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        logger.warning(f"Usuario con ID {user_id} no encontrado.")
        abort(404)
    
    form = UpdateUserForm(original_username=user.username, original_email=user.email)
    
    if form.validate_on_submit():
        logger.debug(f"Actualizando usuario {user.username}")
        
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            user.image_file = picture_file
            logger.info(f"Imagen de perfil actualizada para el usuario {user.username}")

        user.username = form.username.data
        user.email = form.email.data
        user.address = form.address.data
        user.phone = form.phone.data
        user.is_admin = form.is_admin.data
        user.save()
        
        flash('Usuario actualizado exitosamente', 'success')
        logger.info(f"Usuario {user.username} actualizado exitosamente.")
        return redirect(url_for('admin.list_users'))

    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.address.data = user.address
        form.phone.data = user.phone
        form.is_admin.data = user.is_admin
    
    image_file = url_for('static', filename='profile_pics/' + user.image_file)
    return render_template('admin/edit_user.html', title='Editar Usuario', form=form, image_file=image_file, user=user)

@admin_bp.route("/user/<user_id>/delete", methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        logging.warning(f"Intento de eliminar usuario no existente con ID {user_id}")
        abort(404)
    
    form = DeleteAccountForm()
    if form.validate_on_submit():
        user.delete()
        flash('Usuario eliminado exitosamente', 'success')
        logging.info(f"Usuario con ID {user_id} eliminado exitosamente.")
        return redirect(url_for('admin.list_users'))

    return render_template('admin/delete_user.html', user=user, form=form)

@admin_bp.route("/admin/user/search", methods=['GET', 'POST'])
@login_required
@admin_required
def search_user():
    form = SearchUserForm()
    user = None
    if form.validate_on_submit():
        search_query = form.search_query.data.strip()
        normalized_query = unidecode.unidecode(search_query).lower()
        user = User.objects(Q(username__iexact=normalized_query) | Q(email__iexact=normalized_query)).first()
        
        if user:
            logger.info(f"Usuario encontrado: {user.username} con ID {user.id}")
            return redirect(url_for('admin.edit_user', user_id=user.id))
        else:
            flash('Usuario no encontrado', 'danger')
            logger.warning(f"No se encontró ningún usuario con el término de búsqueda: {search_query}")
    
    return render_template('admin/search_user.html', title='Buscar Usuario', form=form, user=user)

@admin_bp.route("/admin/user/<user_id>/view", methods=['GET'])
@login_required
@admin_required
def view_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        logging.warning(f"Usuario con ID {user_id} no encontrado para vista.")
        abort(404)
    
    return render_template('admin/view_user.html', title='Ver Usuario', user=user)

@admin_bp.route("/admin/user/<user_id>/containers", methods=['GET'])
@login_required
@admin_required
def list_user_containers(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        logger.warning(f"Usuario con ID {user_id} no encontrado.")
        abort(404)
    
    containers = Container.objects(user=user)
    return render_template('admin/list_user_containers.html', title='Contenedores de Usuario', user=user, containers=containers)

@admin_bp.route("/admin/containers", methods=['GET', 'POST'])
@login_required
@admin_required
def admin_search_containers():
    form = SearchContainerForm()
    containers = []
    
    if form.validate_on_submit():
        search_query = form.search_query.data
        normalized_query = unidecode.unidecode(search_query).lower()

        # Realizar la búsqueda ignorando mayúsculas, minúsculas y acentos
        containers = Container.objects(
            Q(name__icontains=normalized_query) |
            Q(location__icontains=normalized_query) |
            Q(items__icontains=normalized_query)
        )
        
        if not containers:
            flash('No se encontraron contenedores', 'info')
            logging.info(f"No se encontraron contenedores con la búsqueda: {search_query}")
    
    return render_template('admin/admin_search_containers.html', title='Buscar Contenedores', form=form, containers=containers)

@admin_bp.route("/admin/containers/<container_id>/edit", methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_container(container_id):
    logging.debug(f"Entrando en admin_edit_container con container_id={container_id}")
    
    container = Container.objects(id=container_id).first()
    if not container:
        logging.warning(f"Contenedor con ID {container_id} no encontrado.")
        abort(404)
    
    form = ContainerForm()
    if form.validate_on_submit():
        logging.debug(f"Formulario validado exitosamente para el contenedor {container.name}")

        container.name = form.name.data
        container.location = form.location.data
        container.items = [item.strip() for item in form.items.data.split(",")]

        if form.pictures.data:
            logging.debug("Intentando guardar imágenes del contenedor...")
            picture_files = []
            for picture in form.pictures.data:
                if isinstance(picture, FileStorage) and picture.filename != '':
                    try:
                        picture_file = save_container_picture(picture)
                        logging.debug(f"Imagen guardada: {picture_file}")
                        picture_files.append(picture_file)
                    except Exception as e:
                        logging.error(f"Error guardando la imagen: {e}")
            container.image_file = picture_files
        
        container.save()
        logging.info(f"Contenedor {container.name} actualizado y guardado exitosamente.")
        flash("Contenedor actualizado exitosamente", 'success')
        return redirect(url_for('admin.admin_search_containers'))
    
    elif request.method == 'GET':
        logging.debug("GET request recibido, llenando el formulario con datos del contenedor.")
        form.name.data = container.name
        form.location.data = container.location
        form.items.data = ", ".join(container.items)
    
    return render_template('admin/edit_container.html', title='Editar Contenedor', form=form, container=container)

@admin_bp.route('/admin_search_containers', methods=['GET', 'POST'], endpoint='admin_search_containers_view')
@login_required
def admin_search_containers_view():
    form = SearchContainerForm()
    containers = []
    if form.validate_on_submit():
        search_query = form.search_query.data.strip()
        try:
            containers = Container.objects(name__icontains=search_query)
        except mongoengine.errors.DoesNotExist:
            flash('No se encontraron contenedores.', 'danger')
        except Exception as e:
            flash(f'Error al buscar contenedores: {str(e)}', 'danger')
    
    # Verificar la existencia de los usuarios
    valid_containers = []
    for container in containers:
        try:
            container.user.username  # Intentar acceder al usuario
            valid_containers.append(container)
        except mongoengine.errors.DoesNotExist:
            flash(f'Contenedor {container.name} tiene un usuario no válido.', 'warning')
    
    return render_template('admin/admin_search_containers.html', title='Buscar Contenedores', form=form, containers=valid_containers)

@admin_bp.route("/admin/containers/<container_id>/delete", methods=['POST'])
@login_required
@admin_required
def admin_delete_container(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        logging.warning(f"Intento de eliminar contenedor no existente con ID {container_id}")
        abort(404)
    
    container.delete()
    flash("Contenedor eliminado correctamente", 'success')
    logging.info(f"Contenedor con ID {container_id} eliminado exitosamente.")
    return redirect(url_for('admin.admin_search_containers_view'))