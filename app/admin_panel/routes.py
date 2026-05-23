from functools import wraps
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from app.admin_panel import admin_bp
from app.admin_panel.forms import ModuleForm, LessonForm
from app.models import User, Module, Lesson, UserProgress
from app import db
from app.cloudinary_utils import upload_image, delete_image


def admin_required(f):
    """Decorator that restricts access to admin users."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ──────────────────────────────────────────────
#  Dashboard
# ──────────────────────────────────────────────

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with statistics."""
    stats = {
        'total_users': User.query.filter_by(is_admin=False).count(),
        'active_users': User.query.filter_by(is_admin=False, is_active=True).count(),
        'total_modules': Module.query.count(),
        'published_modules': Module.query.filter_by(is_published=True).count(),
        'total_lessons': Lesson.query.count(),
        'published_lessons': Lesson.query.filter_by(is_published=True).count(),
        'total_completions': UserProgress.query.filter_by(completed=True).count(),
    }
    recent_users = User.query.filter_by(is_admin=False).order_by(
        User.created_at.desc()
    ).limit(5).all()

    return render_template('admin/dashboard.html', stats=stats,
                           recent_users=recent_users)


# ──────────────────────────────────────────────
#  User Management
# ──────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def users():
    """List all users."""
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.filter_by(is_admin=False).order_by(
        User.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/users.html', users=users_pagination)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    """Toggle user active status."""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Não é possível desativar um administrador.', 'error')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'ativado' if user.is_active else 'desativado'
    flash(f'Usuário {user.username} foi {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Não é possível deletar um administrador.', 'error')
        return redirect(url_for('admin.users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'Usuário {username} foi deletado.', 'success')
    return redirect(url_for('admin.users'))


# ──────────────────────────────────────────────
#  Module Management
# ──────────────────────────────────────────────

@admin_bp.route('/modules')
@admin_required
def modules():
    """List all modules."""
    all_modules = Module.query.order_by(Module.order).all()
    return render_template('admin/modules.html', modules=all_modules)


@admin_bp.route('/modules/new', methods=['GET', 'POST'])
@admin_required
def new_module():
    """Create a new module."""
    form = ModuleForm()
    if form.validate_on_submit():
        module = Module(
            title=form.title.data.strip(),
            description=form.description.data or '',
            order=form.order.data or 0,
            is_published=form.is_published.data
        )

        # Handle thumbnail upload to Cloudinary
        if form.thumbnail.data:
            result = upload_image(form.thumbnail.data, folder='gdev-tutorial/modules')
            if result:
                module.thumbnail_url = result['url']
                module.thumbnail_public_id = result['public_id']
                flash('Thumbnail enviada com sucesso!', 'info')
            else:
                flash('Erro ao enviar thumbnail. O módulo foi criado sem imagem.', 'warning')

        db.session.add(module)
        db.session.commit()
        flash(f'Módulo "{module.title}" criado com sucesso!', 'success')
        return redirect(url_for('admin.modules'))

    return render_template('admin/module_form.html', form=form, title='Novo Módulo')


@admin_bp.route('/modules/<int:module_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_module(module_id):
    """Edit a module."""
    module = Module.query.get_or_404(module_id)
    form = ModuleForm(obj=module)

    if form.validate_on_submit():
        module.title = form.title.data.strip()
        module.description = form.description.data or ''
        module.order = form.order.data or 0
        module.is_published = form.is_published.data

        # Handle thumbnail upload to Cloudinary (replace old one if exists)
        if form.thumbnail.data:
            # Delete old thumbnail from Cloudinary if it exists
            if module.thumbnail_public_id:
                delete_image(module.thumbnail_public_id)

            result = upload_image(form.thumbnail.data, folder='gdev-tutorial/modules')
            if result:
                module.thumbnail_url = result['url']
                module.thumbnail_public_id = result['public_id']
                flash('Thumbnail atualizada com sucesso!', 'info')
            else:
                flash('Erro ao enviar nova thumbnail.', 'warning')

        db.session.commit()
        flash(f'Módulo "{module.title}" atualizado!', 'success')
        return redirect(url_for('admin.modules'))

    return render_template('admin/module_form.html', form=form,
                           title='Editar Módulo', module=module)


@admin_bp.route('/modules/<int:module_id>/delete', methods=['POST'])
@admin_required
def delete_module(module_id):
    """Delete a module and its lessons."""
    module = Module.query.get_or_404(module_id)
    title = module.title

    # Delete thumbnail from Cloudinary if it exists
    if module.thumbnail_public_id:
        delete_image(module.thumbnail_public_id)

    db.session.delete(module)
    db.session.commit()
    flash(f'Módulo "{title}" e suas aulas foram deletados.', 'success')
    return redirect(url_for('admin.modules'))


# ──────────────────────────────────────────────
#  Lesson Management
# ──────────────────────────────────────────────

@admin_bp.route('/lessons')
@admin_required
def lessons():
    """List all lessons."""
    all_lessons = Lesson.query.order_by(Lesson.module_id, Lesson.order).all()
    return render_template('admin/lessons.html', lessons=all_lessons)


@admin_bp.route('/lessons/new', methods=['GET', 'POST'])
@admin_required
def new_lesson():
    """Create a new lesson."""
    form = LessonForm()
    form.module_id.choices = [
        (m.id, m.title) for m in Module.query.order_by(Module.order).all()
    ]

    if form.validate_on_submit():
        lesson = Lesson(
            module_id=form.module_id.data,
            title=form.title.data.strip(),
            description=form.description.data or '',
            video_url=form.video_url.data or '',
            content=form.content.data or '',
            order=form.order.data or 0,
            duration_minutes=form.duration_minutes.data or 0,
            is_published=form.is_published.data
        )
        db.session.add(lesson)
        db.session.commit()
        flash(f'Aula "{lesson.title}" criada com sucesso!', 'success')
        return redirect(url_for('admin.lessons'))

    return render_template('admin/lesson_form.html', form=form, title='Nova Aula')


@admin_bp.route('/lessons/<int:lesson_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_lesson(lesson_id):
    """Edit a lesson."""
    lesson = Lesson.query.get_or_404(lesson_id)
    form = LessonForm(obj=lesson)
    form.module_id.choices = [
        (m.id, m.title) for m in Module.query.order_by(Module.order).all()
    ]

    if form.validate_on_submit():
        lesson.module_id = form.module_id.data
        lesson.title = form.title.data.strip()
        lesson.description = form.description.data or ''
        lesson.video_url = form.video_url.data or ''
        lesson.content = form.content.data or ''
        lesson.order = form.order.data or 0
        lesson.duration_minutes = form.duration_minutes.data or 0
        lesson.is_published = form.is_published.data
        db.session.commit()
        flash(f'Aula "{lesson.title}" atualizada!', 'success')
        return redirect(url_for('admin.lessons'))

    return render_template('admin/lesson_form.html', form=form,
                           title='Editar Aula', lesson=lesson)


@admin_bp.route('/lessons/<int:lesson_id>/delete', methods=['POST'])
@admin_required
def delete_lesson(lesson_id):
    """Delete a lesson."""
    lesson = Lesson.query.get_or_404(lesson_id)
    title = lesson.title
    db.session.delete(lesson)
    db.session.commit()
    flash(f'Aula "{title}" foi deletada.', 'success')
    return redirect(url_for('admin.lessons'))
