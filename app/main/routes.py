from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, send_file, jsonify, current_app, session
from flask_login import current_user, login_required
import os
import qrcode
import logging
import logging.handlers
import re
from datetime import datetime
from werkzeug.datastructures import FileStorage
from mongoengine.errors import NotUniqueError, DoesNotExist
from flask_mail import Message

from app.models import Container
from app.forms import ContainerForm, EditContainerForm, DeleteImageForm, SearchContainerForm, ContactForm
from app.utils import save_container_picture, handle_errors, normalize_name
from app.extensions import mail

main_bp = Blueprint('main', __name__)

# Configuración del logger
def setup_logger():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    return logger

logger = setup_logger()

# Funciones auxiliares
def generate_qr_code(container_data, safe_name):
    """Genera y guarda un código QR para un contenedor."""
    try:
        qr_data = (
            f"Contenedor: {container_data['name']}\n"
            f"Ubicación: {container_data['location']}\n"
            f"Objetos: {container_data['items']}"
        )
        qr_img_path = os.path.join(
            current_app.root_path, 'static', 'qr_codes', f"{safe_name}.png"
        )
        qr_img = qrcode.make(qr_data)
        qr_img.save(qr_img_path)
        return f"{safe_name}.png"
    except Exception as e:
        logger.error(f"Error generando código QR: {e}")
        raise

def process_container_images(form_pictures):
    """Procesa y guarda las imágenes del contenedor."""
    picture_files = []
    for picture in form_pictures:
        if isinstance(picture, FileStorage) and picture.filename:
            try:
                picture_file = save_container_picture(picture)
                if picture_file:
                    picture_files.append(picture_file)
            except Exception as e:
                logger.error(f"Error guardando imagen {picture.filename}: {e}")
                raise
    return picture_files

# Rutas básicas
@main_bp.route("/")
@main_bp.route("/home")
def home():
    try:
        session.pop('show_welcome_modal', None)
        current_year = datetime.now().year
        return render_template('home.html', title='Inicio', current_year=current_year)
    except Exception as e:
        logger.error(f"Error en la ruta home: {e}")
        raise

@main_bp.route("/about")
def about():
    return render_template('about.html', title='Acerca de')

@main_bp.route("/welcome")
@login_required
def welcome():
    return render_template('welcome.html')

# Rutas de contenedores
@main_bp.route('/create_container', methods=['GET', 'POST'])
@login_required
def create_container():
    form = ContainerForm()
    if form.validate_on_submit():
        try:
            # Procesar imágenes
            picture_files = process_container_images(form.pictures.data)
            
            # Generar nombre seguro para QR
            safe_name = re.sub(r'[^\w\s-]', '', form.name.data).strip().replace(' ', '_')
            
            # Generar QR
            qr_filename = generate_qr_code({
                'name': form.name.data,
                'location': form.location.data,
                'items': form.items.data
            }, safe_name)
            
            # Crear contenedor
            container = Container(
                name=form.name.data,
                location=form.location.data,
                items=[item.strip() for item in form.items.data.split(",")],
                image_files=picture_files,
                qr_image=qr_filename,
                user=current_user._get_current_object()
            )
            
            container.save()
            flash('Contenedor creado exitosamente.', 'success')
            return redirect(url_for('main.container_detail', container_id=container.id))
            
        except NotUniqueError:
            flash('El nombre del contenedor ya está en uso.', 'danger')
        except Exception as e:
            logger.error(f"Error creando contenedor: {e}")
            flash('Error al crear el contenedor.', 'danger')
    
    return render_template('create_container.html', form=form)

@main_bp.route("/containers/<container_id>/edit", methods=["GET", "POST"])
@login_required
def edit_container(container_id):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            flash("Contenedor no encontrado", "danger")
            return redirect(url_for("main.list_containers"))

        if str(container.user.id) != str(current_user.id):
            flash("No tienes permiso para editar este contenedor", "danger")
            return redirect(url_for("main.list_containers"))

        form = EditContainerForm(original_container=container, obj=container)
        delete_form = DeleteImageForm()

        if request.method == "GET":
            form.items.data = ", ".join(container.items) if container.items else ""
            return render_template(
                "edit_container.html",
                container=container,
                form=form,
                delete_form=delete_form
            )

        if form.validate_on_submit():
            try:
                updates = {
                    "name": form.name.data.strip(),
                    "location": form.location.data.strip(),
                    "items": [item.strip() for item in form.items.data.split(',') if item.strip()]
                }

                # Procesar nuevas imágenes
                if form.pictures.data:
                    new_images = process_container_images(form.pictures.data)
                    if new_images:
                        updates["image_files"] = container.image_files + new_images

                # Actualizar contenedor
                container.update(**{f"set__{k}": v for k, v in updates.items()})
                container.reload()

                flash("Contenedor actualizado correctamente", "success")
                return redirect(url_for("main.container_detail", container_id=container.id))

            except Exception as e:
                logger.error(f"Error actualizando contenedor: {e}")
                flash("Error al actualizar el contenedor", "danger")

        return render_template(
            "edit_container.html",
            container=container,
            form=form,
            delete_form=delete_form
        )

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        flash("Ha ocurrido un error inesperado", "danger")
        return redirect(url_for("main.list_containers"))

# Rutas de visualización y listado
@main_bp.route("/containers/<container_id>")
@login_required
def container_detail(container_id):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            logger.warning(f"Contenedor {container_id} no encontrado")
            abort(404)
        
        if container.user.id != current_user.id and not current_user.is_admin:
            logger.warning(f"Acceso no autorizado al contenedor {container_id}")
            abort(403)
            
        return render_template('container_detail.html', container=container)
    except Exception as e:
        logger.error(f"Error en container_detail: {e}")
        flash("Error al cargar los detalles del contenedor", "danger")
        return redirect(url_for('main.list_containers'))

@main_bp.route("/containers")
@login_required
def list_containers():
    try:
        form = SearchContainerForm()
        search_query = request.args.get('search_query', '').strip()
        
        containers = Container.objects(user=current_user._get_current_object())
        if search_query:
            containers = containers.filter(name__icontains=search_query)
            
        return render_template('list_containers.html', containers=containers, form=form)
    except Exception as e:
        logger.error(f"Error en list_containers: {e}")
        flash("Error al cargar la lista de contenedores", "danger")
        return redirect(url_for('main.home'))

@main_bp.route("/containers/<container_id>/print_detail", methods=['GET'])
@login_required
def print_detail(container_id):
    try:
        container = Container.objects(id=container_id, is_deleted=False).first()
        if not container:
            logging.warning(f"Intento de acceder a un contenedor no existente con ID {container_id}")
            abort(404)

        # Verificar permisos: permitir acceso si el usuario es el propietario o es administrador
        if container.user.id != current_user.id and not current_user.is_admin:
            logging.warning(f"Acceso no autorizado al contenedor {container_id} por el usuario {current_user.id}")
            abort(403)

        # Verificar imágenes válidas
        valid_images = []
        for image in container.image_files or []:  # Asegurarse de que image_files no sea None
            image_path = os.path.join(current_app.root_path, 'static', 'container_pics', image)
            if os.path.exists(image_path):
                valid_images.append(image)
            else:
                logging.warning(f"Imagen no encontrada: {image_path}")

        # Asegúrate de que items sea una lista
        items_list = []
        if container.items:
            if callable(container.items):
                items_list = container.items()  # Llama al método si es necesario
            elif isinstance(container.items, (list, tuple)):
                items_list = container.items
            elif isinstance(container.items, str):
                items_list = [item.strip() for item in container.items.split(',') if item.strip()]

        # Crear el diccionario con los datos del contenedor
        container_data = {
            'id': str(container.id),
            'name': container.name,
            'location': container.location,
            'items': items_list,
            'image_files': valid_images,
            'qr_image': container.qr_image,
            'created_at': container.created_at
        }

        logging.debug(f"Container data prepared: {container_data}")

        return render_template(
            'print_detail.html', 
            title='Imprimir Detalle', 
            container=container_data
        )
    except Exception as e:
        logging.error(f"Error en print_detail: {str(e)}")
        flash("Error al preparar la vista de impresión", "danger")
        return redirect(url_for('main.list_containers'))

def print_detail(detail):
    try:
        # Asegúrate de que 'detail' es un objeto que tiene longitud
        if isinstance(detail, (list, str)):
            print(len(detail))
        else:
            print("El objeto no tiene longitud")
    except Exception as e:
        app.logger.error(f"Error en print_detail: {e}")

# Rutas de manipulación de contenedores
@main_bp.route("/containers/<container_id>/delete", methods=['POST'])
@login_required
def delete_container(container_id):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            abort(404, description="Contenedor no encontrado")
        
        if container.user.id != current_user.id and not current_user.is_admin:
            logger.warning(f"Intento de eliminación no autorizado del contenedor {container_id}")
            abort(403)

        # Eliminar imágenes asociadas
        for image in container.image_files:
            try:
                image_path = os.path.join(current_app.root_path, 'static', 'container_pics', image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                logger.warning(f"Error al eliminar imagen {image}: {e}")

        # Eliminar código QR
        if container.qr_image:
            try:
                qr_path = os.path.join(current_app.root_path, 'static', 'qr_codes', container.qr_image)
                if os.path.exists(qr_path):
                    os.remove(qr_path)
            except Exception as e:
                logger.warning(f"Error al eliminar QR {container.qr_image}: {e}")

        container.delete()
        flash('Contenedor eliminado exitosamente', 'success')
        return redirect(url_for('main.list_containers'))
    except Exception as e:
        logger.error(f"Error al eliminar contenedor: {e}")
        flash('Error al eliminar el contenedor', 'danger')
        return redirect(url_for('main.list_containers'))

@main_bp.route("/containers/<container_id>/delete_image/<image_name>", methods=["POST"])
@login_required
def delete_container_image(container_id, image_name):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            return jsonify({"success": False, "error": "Contenedor no encontrado"}), 404

        if container.user.id != current_user.id and not current_user.is_admin:
            return jsonify({"success": False, "error": "No autorizado"}), 403

        # Eliminar archivo físico
        image_path = os.path.join(current_app.root_path, 'static/container_pics', image_name)
        if os.path.exists(image_path):
            os.remove(image_path)

        # Actualizar base de datos
        container.update(pull__image_files=image_name)
        container.reload()

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error eliminando imagen: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Rutas de descarga y QR
@main_bp.route("/containers/<container_id>/download_qr")
@login_required
def download_qr(container_id):
    try:
        container = Container.objects(id=container_id).first()
        if not container:
            logger.warning(f"Contenedor {container_id} no encontrado")
            abort(404)

        if container.user.id != current_user.id and not current_user.is_admin:
            logger.warning(f"Acceso no autorizado al QR del contenedor {container_id}")
            abort(403)

        qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container.qr_image)
        if not os.path.exists(qr_path):
            logger.error(f"QR no encontrado: {container.qr_image}")
            flash('Código QR no encontrado', 'danger')
            return redirect(url_for('main.container_detail', container_id=container_id))

        return send_file(qr_path, as_attachment=True, download_name=container.qr_image)
    except Exception as e:
        logger.error(f"Error en download_qr: {e}")
        flash("Error al descargar el código QR", "danger")
        return redirect(url_for('main.container_detail', container_id=container_id))

# Ruta de contacto
@main_bp.route("/contacto", methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            msg = Message(
                subject=f"Nuevo mensaje de contacto de {form.name.data}",
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[current_app.config['MAIL_DEFAULT_SENDER']],
                reply_to=form.email.data,
                body=f'''
                Nombre: {form.name.data}
                Email: {form.email.data}
                Mensaje:
                {form.message.data}
                '''
            )
            mail.send(msg)
            flash('Mensaje enviado exitosamente!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            flash('Error al enviar el mensaje', 'danger')
    return render_template('contacto.html', form=form)

# Ruta de vista previa
@main_bp.route("/containers/<container_id>/preview", methods=["GET"])
@login_required
def container_preview(container_id):
    try:
        container = Container.objects.get(id=container_id)
        
        # Verificar si el contenedor existe
        if not container:
            logger.warning(f"Contenedor {container_id} no encontrado")
            flash("Contenedor no encontrado", "danger")
            return redirect(url_for('main.list_containers'))
        
        # Verificar si el usuario tiene acceso
        try:
            if str(container.user.id) != str(current_user.id) and not current_user.is_admin:
                logger.warning(f"Acceso no autorizado al contenedor {container_id}")
                flash("No tienes permiso para ver este contenedor", "danger")
                return redirect(url_for('main.list_containers'))
        except DoesNotExist:
            logger.error(f"Usuario no encontrado para el contenedor {container_id}")
            flash("Error al verificar permisos", "danger")
            return redirect(url_for('main.list_containers'))
        
        return render_template('container_preview.html', container=container)
    
    except DoesNotExist:
        logger.error(f"Contenedor {container_id} no encontrado")
        flash("Contenedor no encontrado", "danger")
        return redirect(url_for('main.list_containers'))
    except Exception as e:
        logger.error(f"Error en container_preview: {str(e)}")
        flash("Error al cargar la vista previa", "danger")
        return redirect(url_for('main.list_containers'))

# Manejadores de error
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Ruta para habilitar la Pro Version
@main_bp.route('/enable_pro', methods=['POST'])
def enable_pro():
    """
    Endpoint to enable Pro version for the user.
    """
    # Logic to enable Pro version goes here
    return jsonify({'message': 'Pro version enabled successfully!'})