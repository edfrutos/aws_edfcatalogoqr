from flask import Blueprint, render_template, url_for, flash, redirect, request
from app.forms import UpdateUserForm, SearchContainerForm
from app.models import User, Container
from flask_login import login_required, current_user
from app import db, bcrypt
from mongoengine.queryset.visitor import Q  # Importar Q

admin = Blueprint('admin', __name__)

@admin.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.home'))
    users = User.objects.all()
    return render_template('admin_users.html', title='Manage Users', users=users)

@admin.route("/admin/user/<user_id>", methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.home'))
    user = User.objects.get_or_404(id=user_id)
    form = UpdateUserForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.save()
        flash('The user has been updated!', 'success')
        return redirect(url_for('admin.admin_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
    return render_template('update_user.html', title='Update User', form=form)

@admin.route("/admin/containers", methods=['GET', 'POST'])
@login_required
def admin_search_containers():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.home'))
    form = SearchContainerForm()
    containers = []
    if form.validate_on_submit():
        search_query = form.search_query.data
        containers = Container.objects(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(items__icontains=search_query)
        )
    return render_template('admin_search_containers.html', title='Search Containers', form=form, containers=containers)