from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import User
from app.models import Container
from app.models import Image
from app.forms import UpdateUserForm, SearchContainerForm

admin = Blueprint('admin', __name__)

@admin.route("/admin/users")
@login_required
def list_users():
    users = User.objects.all()
    return render_template('admin_users.html', title='List Users', users=users)

@admin.route("/admin/user/<user_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.objects(id=user_id).first()
    if user is None:
        abort(404)
    form = UpdateUserForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.save()
        flash('User has been updated!', 'success')
        return redirect(url_for('admin.list_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    return render_template('edit_user.html', title='Edit User', form=form, user=user)

@admin.route("/admin/containers", methods=['GET', 'POST'])
@login_required
def admin_search_containers():
    form = SearchContainerForm()
    containers = []
    if form.validate_on_submit():
        search_query = form.search.data
        containers = Container.objects(name__icontains=search_query)
    return render_template('admin_search_containers.html', title='Search Containers', form=form, containers=containers)