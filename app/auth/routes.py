from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User
from app import db


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Sua conta está desativada. Entre em contato com o administrador.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            flash(f'Bem-vindo de volta, {user.username}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email ou senha incorretos.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower().strip(),
            password_hash=generate_password_hash(form.password.data),
            is_admin=False,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Conta criada com sucesso! Bem-vindo ao GDev Tutorial!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.index'))
