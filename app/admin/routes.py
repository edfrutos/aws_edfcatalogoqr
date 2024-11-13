from flask import (
    Blueprint, render_template, url_for, flash, redirect, request, 
    current_app, abort, jsonify
)
from flask_login import current_user, login_required
from app.models import User, Container
from app.utils import admin_required
from datetime import datetime
from mongoengine.errors import ValidationError, DoesNotExist
from mongoengine.queryset.visitor import Q
from bson import ObjectId
import logging.handlers

# Configurar logger específico para admin
logger = logging.getLogger('admin')
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    'logs/admin.log', 
    maxBytes=10000, 
    backupCount=5
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Crear el Blueprint
admin_bp = Blueprint('admin', __name__)

def is_valid_objectid(id_str):
    """Validar si una cadena es un ObjectId válido."""
    try:
        ObjectId(id_str)
        return True
    except:
        return False

@admin_bp.route("/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Vista del panel de administración principal."""
    try:
        total_users = User.objects.count()
        total_containers = Container.objects.count()
        recent_users = User.objects.order_by('-date_joined')[:5]
        recent_containers = Container.objects.order_by('-date_created')[:5]
        
        stats = {
            'total_users': total_users,
            'total_containers': total_containers,
            'active_users': User.objects(is_active=True).count(),
            'inactive_users': User.objects(is_active=False).count()
        }
        
        return render_template(
            'admin/dashboard.html',
            stats=stats,
            recent_users=recent_users,
            recent_containers=recent_containers,
            title='Panel de Administración'
        )
    except Exception as e:
        logger.error(f"Error en el dashboard de administración: {str(e)}")
        flash('Error al cargar el dashboard', 'danger')
        return redirect(url_for('main.home'))

@admin_bp.route("/users")
@login_required
@admin_required
def user_list():
    """Lista de usuarios para administración."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Filtros
        search_query = request.args.get('search', '')
        status_filter = request.args.get('status')
        
        # Construir query base
        users_query = User.objects
        
        # Aplicar filtros
        if search_query:
            users_query = users_query.filter(
                Q(username__icontains=search_query) | 
                Q(email__icontains=search_query)
            )
        
        if status_filter:
            users_query = users_query.filter(is_active=status_filter == 'active')
        
        # Obtener total y usuarios paginados
        total_users = users_query.count()
        users = users_query.order_by('-date_joined').skip(offset).limit(per_page)
        
        return render_template(
            'admin/user_list.html',
            users=users,
            total_users=total_users,
            page=page,
            per_page=per_page,
            total_pages=(total_users + per_page - 1) // per_page,
            title='Administración de Usuarios'
        )
    except Exception as e:
        logger.error(f"Error en la lista de usuarios: {str(e)}")
        flash('Error al cargar la lista de usuarios', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route("/users/<user_id>", methods=['GET', 'POST'])
@login_required
@admin_required
def user_detail(user_id):
    """Vista detallada y edición de usuario."""
    if not is_valid_objectid(user_id):
        flash('ID de usuario inválido', 'danger')
        return redirect(url_for('admin.user_list'))
    
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            user.username = request.form.get('username', user.username)
            user.email = request.form.get('email', user.email)
            user.is_active = 'is_active' in request.form
            user.is_admin = 'is_admin' in request.form
            
            try:
                user.save()
                flash('Usuario actualizado exitosamente', 'success')
            except ValidationError as e:
                flash(f'Error de validación: {str(e)}', 'danger')
            
            return redirect(url_for('admin.user_detail', user_id=user_id))
        
        # Obtener contenedores del usuario
        user_containers = Container.objects(user=user).order_by('-date_created')
        
        return render_template(
            'admin/user_detail.html',
            user=user,
            containers=user_containers,
            title=f'Usuario: {user.username}'
        )
    except DoesNotExist:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('admin.user_list'))
    except Exception as e:
        logger.error(f"Error en detalles de usuario: {str(e)}")
        flash('Error al procesar la solicitud', 'danger')
        return redirect(url_for('admin.user_list'))

@admin_bp.route("/users/<user_id>/delete", methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Eliminar usuario."""
    if not is_valid_objectid(user_id):
        return jsonify({'success': False, 'error': 'ID de usuario inválido'}), 400
    
    try:
        user = User.objects.get(id=user_id)
        
        # Evitar auto-eliminación
        if str(user.id) == str(current_user.id):
            return jsonify({
                'success': False, 
                'error': 'No puedes eliminar tu propio usuario'
            }), 400
        
        # Eliminar contenedores asociados
        Container.objects(user=user).delete()
        
        # Eliminar usuario
        user.delete()
        
        return jsonify({'success': True})
    except DoesNotExist:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    except Exception as e:
        logger.error(f"Error eliminando usuario: {str(e)}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@admin_bp.route("/containers")
@login_required
@admin_required
def container_list():
    """Lista de contenedores para administración."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Filtros
        search_query = request.args.get('search', '')
        user_filter = request.args.get('user')
        
        # Construir query base
        containers_query = Container.objects
        
        # Aplicar filtros
        if search_query:
            containers_query = containers_query.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        if user_filter and is_valid_objectid(user_filter):
            containers_query = containers_query.filter(user=user_filter)
        
        # Obtener total y contenedores paginados
        total_containers = containers_query.count()
        containers = containers_query.order_by('-date_created').skip(offset).limit(per_page)
        
        # Obtener lista de usuarios para el filtro
        users = User.objects.all()
        
        return render_template(
            'admin/container_list.html',
            containers=containers,
            users=users,
            total_containers=total_containers,
            page=page,
            per_page=per_page,
            total_pages=(total_containers + per_page - 1) // per_page,
            current_user_filter=user_filter,
            title='Administración de Contenedores'
        )
    except Exception as e:
        logger.error(f"Error en la lista de contenedores: {str(e)}")
        flash('Error al cargar la lista de contenedores', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route("/containers/<container_id>", methods=['GET', 'POST'])
@login_required
@admin_required
def container_detail(container_id):
    """Vista detallada y edición de contenedor."""
    if not is_valid_objectid(container_id):
        flash('ID de contenedor inválido', 'danger')
        return redirect(url_for('admin.container_list'))
    
    try:
        container = Container.objects.get(id=container_id)
        
        if request.method == 'POST':
            container.name = request.form.get('name', container.name)
            container.location = request.form.get('location', container.location)
            container.items = [item.strip() for item in request.form.get('items', '').split(',')]
            
            try:
                container.save()
                flash('Contenedor actualizado exitosamente', 'success')
            except ValidationError as e:
                flash(f'Error de validación: {str(e)}', 'danger')
            
            return redirect(url_for('admin.container_detail', container_id=container_id))
        
        return render_template(
            'admin/container_detail.html',
            container=container,
            title=f'Contenedor: {container.name}'
        )
    except DoesNotExist:
        flash('Contenedor no encontrado', 'danger')
        return redirect(url_for('admin.container_list'))
    except Exception as e:
        logger.error(f"Error en detalles de contenedor: {str(e)}")
        flash('Error al procesar la solicitud', 'danger')
        return redirect(url_for('admin.container_list'))

@admin_bp.route("/containers/<container_id>/delete", methods=['POST'])
@login_required
@admin_required
def delete_container(container_id):
    """Eliminar contenedor."""
    if not is_valid_objectid(container_id):
        return jsonify({'success': False, 'error': 'ID de contenedor inválido'}), 400
    
    try:
        container = Container.objects.get(id=container_id)
        container.delete()
        return jsonify({'success': True})
    except DoesNotExist:
        return jsonify({'success': False, 'error': 'Contenedor no encontrado'}), 404
    except Exception as e:
        logger.error(f"Error eliminando contenedor: {str(e)}")
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

@admin_bp.route("/stats")
@login_required
@admin_required
def admin_stats():
    """Estadísticas del sistema."""
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects(is_active=True).count(),
            'total_containers': Container.objects.count(),
            'containers_today': Container.objects(date_created__gte=today).count(),
        }
        
        # Estadísticas mensuales
        monthly_stats = {
            'users': [],
            'containers': []
        }
        
        # Implementar lógica para estadísticas mensuales aquí
        
        return render_template(
            'admin/stats.html',
            stats=stats,
            monthly_stats=monthly_stats,
            title='Estadísticas del Sistema'
        )
    except Exception as e:
        logger.error(f"Error al cargar estadísticas: {str(e)}")
        flash('Error al cargar las estadísticas', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
