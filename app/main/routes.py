from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, send_file, jsonify, current_app, session
from flask_login import current_user, login_required
import os
import qrcode
import logging
from datetime import datetime
from app.models import Container
from app.forms import (ContainerForm, EditContainerForm, DeleteImageForm, SearchContainerForm, ContactForm)
from app.utils import save_container_picture, handle_errors, normalize_name
from app.extensions import mail
from flask_mail import Message
from werkzeug.datastructures import FileStorage
from mongoengine.errors import NotUniqueError

main_bp = Blueprint('main', __name__)

logger = logging.getLogger(__name__)

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

@main_bp.route("/")
@main_bp.route("/home")
def home():
    try:
        session.pop('show_welcome_modal', None)
        current_year = datetime.now().year
        return render_template('home.html', title='Inicio', current_year=current_year)
    except Exception as e:
        current_app.logger.error(f"Error en la ruta home: {e}")
        raise

@main_bp.route("/about")
def about():
    return render_template('about.html', title='Acerca de')

@main_bp.route("/welcome")
@login_required
def welcome():
    return render_template('welcome.html')

import re  # Asegúrate de tener importada esta librería para limpiar el nombre del archivo QR

@main_bp.route('/create_container', methods=['GET', 'POST'])
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

@main_bp.route("/containers/<container_id>")
@login_required
def container_detail(container_id):
    # Busca el contenedor por ID
    container = Container.objects(id=container_id).first()

    # Si no se encuentra el contenedor, devuelve un error 404
    if not container:
        abort(404)

    # Verifica que el usuario actual sea el propietario del contenedor
    if container.user.id != current_user.id:
        abort(403)

    # Renderiza la plantilla con los detalles del contenedor
    return render_template('container_detail.html', container=container)

@main_bp.route("/containers")
@login_required
def list_containers():
    form = SearchContainerForm()
    search_query = request.args.get('search_query', '')
    containers = Container.objects(user=current_user._get_current_object())
    if search_query:
        containers = containers.filter(name__icontains=search_query)
    return render_template('list_containers.html', containers=containers, form=form)

@main_bp.route("/containers/<container_id>/edit", methods=["GET", "POST"])
@login_required
def edit_container(container_id):
    logger.debug(f"Iniciando edición del contenedor {container_id}")

    try:
        container = Container.objects(id=container_id).first()
        if not container:
            logger.error(f"Contenedor {container_id} no encontrado")
            flash("Contenedor no encontrado", "danger")
            return redirect(url_for("main.list_containers"))

        # Verificar propiedad del contenedor
        if str(container.user.id) != str(current_user.id):
            logger.warning(f"Acceso denegado: Usuario {current_user.id} intentó editar contenedor {container_id}")
            flash("No tienes permiso para editar este contenedor", "danger")
            return redirect(url_for("main.list_containers"))

        form = EditContainerForm(obj=container)
        delete_form = DeleteImageForm()

        # Manejo de solicitud GET
        if request.method == "GET":
            form.items.data = ", ".join(container.items) if container.items else ""
            return render_template(
                "edit_container.html",
                container=container,
                form=form,
                delete_form=delete_form
            )

        # Manejo de solicitud POST
        if form.validate_on_submit():
            try:
                # Preparar actualizaciones
                updates = {
                    "name": form.name.data.strip(),
                    "location": form.location.data.strip(),
                    "items": [item.strip() for item in form.items.data.split(',') if item.strip()]
                }

                # Verificar si existe otro contenedor con el mismo nombre
                existing_container = Container.objects(
                    name=updates["name"], 
                    id__ne=container_id
                ).first()
                
                if existing_container:
                    flash("Ya existe un contenedor con ese nombre", "danger")
                    return render_template(
                        "edit_container.html",
                        container=container,
                        form=form,
                        delete_form=delete_form
                    )

                # Procesar nuevas imágenes
                new_images = []
                if form.pictures.data:
                    for picture in form.pictures.data:
                        if isinstance(picture, FileStorage) and picture.filename:
                            try:
                                filename = save_container_picture(picture)
                                if filename:
                                    new_images.append(filename)
                            except Exception as e:
                                logger.error(f"Error al guardar imagen {picture.filename}: {str(e)}")
                                flash(f"Error al guardar imagen {picture.filename}", "warning")

                # Actualizar el contenedor
                update_data = {
                    "set__name": updates["name"],
                    "set__location": updates["location"],
                    "set__items": updates["items"]
                }

                if new_images:
                    all_images = container.image_files + new_images
                    update_data["set__image_files"] = all_images

                container.update(**update_data)
                container.reload()

                flash("Contenedor actualizado correctamente", "success")
                
                # Manejar respuesta AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        "success": True,
                        "redirect": url_for("main.container_detail", container_id=container.id)
                    })

                return redirect(url_for("main.container_detail", container_id=container.id))

            except Exception as e:
                logger.error(f"Error en la actualización del contenedor: {str(e)}", exc_info=True)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"success": False, "error": "Error al actualizar el contenedor"}), 500
                
                flash("Error al actualizar el contenedor", "danger")
                return render_template(
                    "edit_container.html",
                    container=container,
                    form=form,
                    delete_form=delete_form
                )

        # Manejo de formulario inválido
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
        logger.error(f"Error inesperado en edit_container: {str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "Error inesperado"}), 500
        
        flash("Ha ocurrido un error inesperado", "danger")
        return redirect(url_for("main.list_containers"))


@main_bp.route("/containers/<container_id>/delete", methods=['POST'])
@login_required
def delete_container(container_id):
    container = Container.objects(id=container_id).first_or_404()
    if container.user.id != current_user.id:
        abort(403)
    container.delete()
    flash('Contenedor eliminado!', 'success')
    return redirect(url_for('main.list_containers'))

@main_bp.route("/containers/<container_id>/print_detail")
@login_required
def print_detail(container_id):
    try:
        # Obtener el contenedor
        container = Container.objects(id=container_id).first()
        if not container:
            logger.warning(f"Contenedor con ID {container_id} no encontrado.")
            abort(404)

        # Verificar permisos
        if container.user.id != current_user.id:
            abort(403)

        # Verificar imágenes válidas
        valid_images = []
        for image in container.image_files:
            image_path = os.path.join(current_app.root_path, 'static', 'container_pics', image)
            if os.path.exists(image_path):
                valid_images.append(image)
            else:
                logger.warning(f"Imagen no encontrada: {image_path}")

        # Asegurarse de que los items sean una lista
        try:
            # Si items es una lista, usarla directamente
            items = container.items if isinstance(container.items, (list, tuple)) else []
            
            # Si es un string, convertirlo a lista
            if isinstance(container.items, str):
                items = [item.strip() for item in container.items.split(',')]
                
        except Exception as e:
            logger.error(f"Error procesando items: {str(e)}")
            items = []

        # Crear el diccionario con los datos del contenedor
        container_data = {
            'id': str(container.id),
            'name': container.name,
            'location': container.location,
            'items': items,
            'image_files': valid_images,
            'qr_image': container.qr_image,
            'created_at': container.created_at if hasattr(container, 'created_at') else None
        }

        # Logging para debug
        logger.debug(f"Container data prepared: {container_data}")
        logger.debug(f"Items type: {type(items)}")
        logger.debug(f"Items content: {items}")

        return render_template(
            'print_detail.html', 
            title='Imprimir Detalle', 
            container=container_data
        )
    except Exception as e:
        logger.error(f"Error en print_detail: {str(e)}", exc_info=True)
        flash("Error al preparar la vista de impresión", "danger")
        return redirect(url_for('main.container_detail', container_id=container_id))

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
            current_app.logger.error(f"Error enviando email: {e}")
            flash('Error al enviar el mensaje', 'danger')
    return render_template('contacto.html', form=form)

# Otras rutas relacionadas con contenedores y funcionalidad principal

@main_bp.route("/print_container/<container_id>")
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

@main_bp.route("/containers/<container_id>/delete_image/<image_name>", methods=["POST"])
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

@main_bp.route("/download_container/<container_id>")
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

@main_bp.route("/containers/<container_id>/download_qr")
@login_required
def download_qr(container_id):
    container = Container.objects(id=container_id).first()
    if not container:
        abort(404)
    qr_path = os.path.join(current_app.root_path, 'static/qr_codes', container.qr_image)
    return send_file(qr_path, as_attachment=True)

@main_bp.route("/containers/<container_id>/preview", methods=["GET"])
@login_required
def container_preview(container_id):
    try:
        container = Container.objects.get(id=container_id)
        return render_template('container_preview.html', container=container)
    except Container.DoesNotExist:
        logger.error(f"Contenedor con ID {container_id} no encontrado.")
        abort(404)