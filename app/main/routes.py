from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from app.main import main_bp
from app.main.forms import ProfileForm
from app.models import Module, Lesson, UserProgress
from app import db, csrf
from app.cloudinary_utils import upload_image, delete_image


@main_bp.route('/')
def index():
    """Landing page."""
    # Get published modules count and lessons count for the landing page
    modules_count = Module.query.filter_by(is_published=True).count()
    lessons_count = Lesson.query.filter_by(is_published=True).count()
    total_duration = db.session.query(
        db.func.sum(Lesson.duration_minutes)
    ).filter(Lesson.is_published == True).scalar() or 0

    return render_template('index.html',
                           modules_count=modules_count,
                           lessons_count=lessons_count,
                           total_duration=total_duration)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard."""
    modules = Module.query.filter_by(is_published=True).order_by(Module.order).all()

    # Calculate overall progress
    total_lessons = Lesson.query.filter_by(is_published=True).count()
    completed_lessons = UserProgress.query.filter_by(
        user_id=current_user.id, completed=True
    ).count()
    progress_percent = (
        int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
    )

    return render_template('course/dashboard.html',
                           modules=modules,
                           total_lessons=total_lessons,
                           completed_lessons=completed_lessons,
                           progress_percent=progress_percent)


@main_bp.route('/course/module/<int:module_id>')
@login_required
def module_detail(module_id):
    """Module detail page with lesson list."""
    module = Module.query.get_or_404(module_id)
    if not module.is_published:
        abort(404)

    lessons = module.published_lessons.all()
    return render_template('course/modules.html', module=module, lessons=lessons)


@main_bp.route('/course/lesson/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    """Lesson/video page."""
    lesson = Lesson.query.get_or_404(lesson_id)
    if not lesson.is_published or not lesson.module.is_published:
        abort(404)

    # Get all lessons in this module for navigation
    module_lessons = lesson.module.published_lessons.all()

    # Find previous and next lessons
    current_index = None
    for i, l in enumerate(module_lessons):
        if l.id == lesson.id:
            current_index = i
            break

    prev_lesson = module_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = (
        module_lessons[current_index + 1]
        if current_index is not None and current_index < len(module_lessons) - 1
        else None
    )

    # Check if completed
    progress = current_user.get_progress_for_lesson(lesson_id)
    is_completed = progress.completed if progress else False

    return render_template('course/lesson.html',
                           lesson=lesson,
                           module_lessons=module_lessons,
                           prev_lesson=prev_lesson,
                           next_lesson=next_lesson,
                           is_completed=is_completed)


@main_bp.route('/course/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    """Mark a lesson as completed."""
    lesson = Lesson.query.get_or_404(lesson_id)
    if not lesson.is_published:
        abort(404)

    progress = UserProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lesson_id
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.now(timezone.utc)
        )
        db.session.add(progress)
    else:
        progress.completed = not progress.completed
        progress.completed_at = (
            datetime.now(timezone.utc) if progress.completed else None
        )

    db.session.commit()

    status = 'concluída' if progress.completed else 'marcada como pendente'
    flash(f'Aula "{lesson.title}" {status}!', 'success')
    return redirect(url_for('main.lesson_detail', lesson_id=lesson_id))


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page for editing details and profile picture."""
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()

        # Handle profile picture upload
        if form.profile_pic.data:
            # Delete old profile pic from Cloudinary if exists
            if current_user.profile_pic_public_id:
                delete_image(current_user.profile_pic_public_id)

            # Upload new profile pic
            result = upload_image(form.profile_pic.data, folder='gdev-tutorial/profiles', is_profile=True)
            if result:
                current_user.profile_pic_url = result['url']
                current_user.profile_pic_public_id = result['public_id']
                flash('Sua foto de perfil foi atualizada com sucesso!', 'success')
            else:
                flash('Ocorreu um erro ao enviar sua foto de perfil para o Cloudinary. Verifique suas credenciais.', 'warning')

        db.session.commit()
        flash('Seu perfil foi atualizado com sucesso!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('course/profile.html', form=form)


@main_bp.route('/api/chat', methods=['POST'])
@csrf.exempt
def chat():
    """API endpoint for OpenAI-powered helper chatbot."""
    import os
    import requests
    from flask import jsonify

    # Get user message
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"response": "Por favor, envie uma mensagem válida."}), 400

    # Get OpenAI key from Railway env
    openai_key = os.environ.get('key_1hsfh0hBAoRilfzZ')

    if not openai_key:
        return jsonify({
            "response": "Olá! Eu sou o GDev Helper. No momento, minha chave de acesso à inteligência artificial não está configurada no servidor. Por favor, avise o administrador do site para cadastrar a chave!"
        }), 200

    try:
        # Prepare headers and body for OpenAI API
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        
        # System prompt to give the AI assistant a clear character
        system_prompt = (
            "Você é o 'GDev Helper', o assistente virtual de Inteligência Artificial da plataforma 'GDev Tutorial'. "
            "Seu objetivo é ajudar estudantes e programadores com dúvidas de programação, HTML, CSS, Flask, Banco de Dados, "
            "e navegação na nossa plataforma. "
            "Seja extremamente amigável, prestativo, bem-humorado e use emojis. Responda em português (PT-BR). "
            "Se o usuário pedir códigos, forneça exemplos bem comentados usando markdown."
        )

        payload = {
            "model": "grok-3-mini-fast",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        # Make request to xAI Grok
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            return jsonify({"response": ai_response})
        else:
            print(f"[GDev Helper] Grok API Error Status {response.status_code}: {response.text}")
            return jsonify({
                "response": "Olá! Tive um pequeno problema de comunicação ao processar sua pergunta. Você pode tentar novamente em alguns segundos?"
            }), 200

    except Exception as e:
        print(f"[GDev Helper] Chat Exception: {e}")
        return jsonify({
            "response": "Ops! Ocorreu um erro de conexão de rede com o cérebro da inteligência artificial. Por favor, tente novamente."
        }), 200
