from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app.models import User
from app.forms import (LoginForm, RegistrationForm, UpdateAccountForm,
                      RequestResetForm, ResetPasswordForm, ChangePasswordForm,
                      DeleteAccountForm)
from app.utils import save_profile_picture, send_reset_email
from app.extensions import bcrypt

users_bp = Blueprint('users', __name__)

@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email_or_username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        flash('Email o contraseña incorrectos', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

@users_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, 
                   email=form.email.data, 
                   password=hashed_password)
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            user.image_file = picture_file
        user.save()
        flash('Tu cuenta ha sido creada! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Registro', form=form)

@users_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.logout_page'))

@users_bp.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.address = form.address.data
        current_user.phone = form.phone.data
        current_user.save()
        flash('Tu cuenta ha sido actualizada!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.address.data = current_user.address
        form.phone.data = current_user.phone
    image_file = url_for('static', 
                        filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', 
                         image_file=image_file, form=form)

@users_bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('Se ha enviado un email con instrucciones para resetear tu contraseña.', 'info')
            return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@users_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Token inválido o expirado', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        user.save()
        flash('Tu contraseña ha sido actualizada!', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_password.html', title='Reset Password', form=form)

@users_bp.route("/change_password", methods=['GET', 'POST'])
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

@users_bp.route("/delete_account", methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if form.confirm.data:
            user = current_user._get_current_object()
            # Eliminar contenedores del usuario
            from app.models import Container
            Container.objects(user=user).delete()
            user.delete()
            logout_user()
            flash('Tu cuenta ha sido eliminada', 'success')
            return redirect(url_for('main.home'))
    return render_template('delete_account.html', title='Eliminar Cuenta', form=form)
