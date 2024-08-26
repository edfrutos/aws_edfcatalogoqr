from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import User, Container
from app.forms import UpdateUserForm, SearchContainerForm
from mongoengine.queryset.visitor import Q
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return login_required(decorated_view)

@admin_bp.route('/users')
@admin_required
def list_users():
    users = User.objects.all()
    return render_template('admin/admin_users.html', title='List Users', users=users)

@admin_bp.route('/user/<user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        abort(404)
    form = UpdateUserForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.address = form.address.data
        user.phone = form.phone.data
        user.save()
        flash('User has been updated!', 'success')
        return redirect(url_for('admin_bp.list_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.address.data = user.address
        form.phone.data = user.phone
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/user/<user_id>/view')
@admin_required
def view_user(user_id):
    user = User.objects(id=user_id).first()
    if not user:
        abort(404)
    return render_template('admin/view_user.html', title='View User', user=user)

@admin_bp.route('/containers', methods=['GET', 'POST'])
@admin_required
def admin_search_containers():
    form = SearchContainerForm()
    containers = []
    if form.validate_on_submit():
        search_query = form.search_query.data
        containers = Container.objects(
            Q(name__icontains=search_query) | Q(location__icontains=search_query) | Q(items__icontains=search_query)
        )
    return render_template('admin/admin_search_containers.html', title='Search Containers', form=form, containers=containers)