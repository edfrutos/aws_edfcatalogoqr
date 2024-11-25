from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, send_file, jsonify, current_app, session
from flask_login import current_user, login_required
import os
import qrcode
from datetime import datetime
from app.models import Container
from app.forms import (ContainerForm, EditContainerForm, DeleteImageForm, SearchContainerForm, ContactForm)
from app.utils import save_container_picture, handle_errors, normalize_name
from app.extensions import mail
from flask_mail import Message
from werkzeug.datastructures import FileStorage
from mongoengine.errors import NotUniqueError

main_bp = Blueprint('main', __name__)

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

@main_bp.route('/create_container', methods=['GET', 'POST'])
@login_required
def create_container():
    form = ContainerForm()
    if form.validate_on_submit():
        current_app.logger.info("Creación de contenedor iniciada.")
        pictures = form.pictures.data
        picture_files = []

        for picture in pictures:
            if isinstance(picture, FileStorage) and picture.filename != '':
                try:
                    picture_file = save_container_picture(picture)
                    picture_files.append(picture_file)
                except Exception as e:
                    current_app.logger.error(f"Error al guardar la imagen: {e}")
                    flash('Error al guardar una de las imágenes.', 'danger')
                    return render_template('create_container.html', form=form)

        # Generar QR
        safe_name = normalize_name(form.name.data)
        qr_data = f"Contenedor: {form.name.data}\nUbicación: {form.location.data}\nObjetos: {form.items.data}"
        qr_img_path = os.path.join(current_app.root_path, 'static', 'qr_codes', f"{safe_name}.png")

        try:
            qr_img = qrcode.make(qr_data)
            qr_img.save(qr_img_path)
        except Exception as e:
            current_app.logger.error(f"Error al generar QR: {e}")
            flash('Error al generar el código QR', 'danger')
            return render_template('create_container.html', form=form)

        try:
            container = Container(
                name=form.name.data,
                location=form.location.data,
                items=[item.strip() for item in form.items.data.split(",")],
                image_files=picture_files,
                qr_image=f"{safe_name}.png",
                user=current_user._get_current_object()
            )
            container.save()
            flash('Contenedor creado exitosamente!', 'success')
            return redirect(url_for('main.container_detail', container_id=container.id))
        except NotUniqueError:
            flash('Ya existe un contenedor con ese nombre', 'danger')

    return render_template('create_container.html', form=form)

@main_bp.route("/containers/<container_id>")
@login_required
def container_detail(container_id):
    container = Container.objects(id=container_id).first_or_404()
    if container.user.id != current_user.id:
        abort(403)
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

@main_bp.route("/containers/<container_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_container(container_id):
    container = Container.objects(id=container_id).first_or_404()
    if container.user.id != current_user.id:
        abort(403)
    form = EditContainerForm()
    delete_form = DeleteImageForm()

    if form.validate_on_submit():
        # Actualizar contenedor
        container.name = form.name.data
        container.location = form.location.data
        container.items = [item.strip() for item in form.items.data.split(",")]
        
        if form.pictures.data:
            for picture in form.pictures.data:
                if picture.filename:
                    picture_file = save_container_picture(picture)
                    container.image_files.append(picture_file)
        
        container.save()
        flash('Contenedor actualizado!', 'success')
        return redirect(url_for('main.container_detail', container_id=container.id))
    
    elif request.method == 'GET':
        form.name.data = container.name
        form.location.data = container.location
        form.items.data = ", ".join(container.items)

    return render_template('edit_container.html', 
                         form=form, 
                         container=container, 
                         delete_form=delete_form)

@main_bp.route("/containers/<container_id>/delete", methods=['POST'])
@login_required
def delete_container(container_id):
    container = Container.objects(id=container_id).first_or_404()
    if container.user.id != current_user.id:
        abort(403)
    container.delete()
    flash('Contenedor eliminado!', 'success')
    return redirect(url_for('main.list_containers'))

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
