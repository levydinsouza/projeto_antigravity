from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, abort, request, session
from flask_login import login_required, current_user

from app.main import main_bp
from app.main.forms import ProfileForm
from app.models import Module, Lesson, UserProgress, ModuleQuizCompletion
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
    # Separate required and optional modules
    required_modules = Module.query.filter_by(is_published=True, is_optional=False).order_by(Module.order).all()
    optional_modules = Module.query.filter_by(is_published=True, is_optional=True).order_by(Module.order).all()

    # Calculate progress based on REQUIRED modules only
    required_module_ids = [m.id for m in required_modules]
    if required_module_ids:
        total_lessons = Lesson.query.filter(
            Lesson.is_published == True,
            Lesson.module_id.in_(required_module_ids)
        ).count()
    else:
        total_lessons = 0

    completed_lessons = 0
    if total_lessons > 0:
        completed_lesson_ids = [p.lesson_id for p in UserProgress.query.filter_by(
            user_id=current_user.id, completed=True
        ).all()]
        completed_lessons = Lesson.query.filter(
            Lesson.id.in_(completed_lesson_ids),
            Lesson.is_published == True,
            Lesson.module_id.in_(required_module_ids)
        ).count() if completed_lesson_ids else 0

    progress_percent = (
        int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
    )

    # Check if user completed ALL required courses (quiz passed on every required module)
    all_courses_completed = current_user.has_completed_all_required_courses()

    return render_template('course/dashboard.html',
                           required_modules=required_modules,
                           optional_modules=optional_modules,
                           total_lessons=total_lessons,
                           completed_lessons=completed_lessons,
                           progress_percent=progress_percent,
                           all_courses_completed=all_courses_completed)


@main_bp.route('/course/module/<int:module_id>')
@login_required
def module_detail(module_id):
    """Module detail page with lesson list."""
    module = Module.query.get_or_404(module_id)
    if not module.is_published:
        abort(404)

    lessons = module.published_lessons.all()
    return render_template('course/modules.html', module=module, lessons=lessons)


def get_fallback_quiz(module):
    """Provide default fallback questions for the quiz."""
    title_lower = module.title.lower()
    
    if "iniciante" in title_lower or "zero" in title_lower or "introdução" in title_lower:
        return [
            {
                "id": 1,
                "question": "Qual é a principal forma de programar a lógica de um jogo na GDevelop?",
                "options": [
                    "Escrevendo scripts em C++",
                    "Usando a folha de Eventos visuais (Condições e Ações)",
                    "Digitando linhas de código em Python",
                    "Criando blocos de blueprint da Unreal Engine"
                ],
                "correct_index": 1
            },
            {
                "id": 2,
                "question": "O que acontece na GDevelop se um evento não tiver nenhuma Condição definida?",
                "options": [
                    "As Ações do evento são executadas a cada frame do jogo (Sempre)",
                    "O jogo gera um erro e para de funcionar",
                    "As Ações do evento nunca serão executadas",
                    "O evento é deletado automaticamente"
                ],
                "correct_index": 0
            },
            {
                "id": 3,
                "question": "Onde você adiciona novas imagens, animações e sons na GDevelop?",
                "options": [
                    "No editor de código HTML",
                    "Na lista de variáveis globais",
                    "No painel de Recursos do projeto",
                    "No banco de dados SQL do site"
                ],
                "correct_index": 2
            }
        ]
    elif "movimento" in title_lower or "física" in title_lower or "pathfinding" in title_lower:
        return [
            {
                "id": 1,
                "question": "Para que serve o comportamento (Behavior) de Pathfinding na GDevelop?",
                "options": [
                    "Para fazer um objeto se mover e desviar de obstáculos de forma inteligente",
                    "Para reproduzir uma música de fundo no jogo",
                    "Para criar um sistema de inventário em array",
                    "Para fazer o jogo rodar em 3D nativo"
                ],
                "correct_index": 0
            },
            {
                "id": 2,
                "question": "Se você quer que um objeto funcione como parede ou chão no comportamento de Pathfinding, qual comportamento ele deve ter?",
                "options": [
                    "Platformer Character",
                    "Physics 2.0",
                    "Pathfinding Obstacle (Obstáculo de busca de caminhos)",
                    "Tween"
                ],
                "correct_index": 2
            },
            {
                "id": 3,
                "question": "Qual comportamento nativo da GDevelop é usado para simular gravidade realista, colisões físicas e forças?",
                "options": [
                    "Anchor",
                    "Physics 2.0 (Física 2.0)",
                    "Tween",
                    "Draggable"
                ],
                "correct_index": 1
            }
        ]
    elif "monetiza" in title_lower or "marketing" in title_lower or "negócio" in title_lower:
        return [
            {
                "id": 1,
                "question": "Qual das seguintes alternativas é uma das 4 principais formas de monetizar jogos ensinadas no gdevtutorial.online?",
                "options": [
                    "Vender o código-fonte inteiro para outras engines",
                    "Anúncios integrados (AdMob) e Compras no aplicativo (In-App Purchases)",
                    "Alugar computadores para os jogadores",
                    "Mineração de criptomoedas em segundo plano"
                ],
                "correct_index": 1
            },
            {
                "id": 2,
                "question": "Onde um desenvolvedor indie pode publicar seu jogo web de forma gratuita e aceitar doações dos jogadores?",
                "options": [
                    "Steam (exige pagamento da taxa do Steam Direct)",
                    "Newgrounds ou Itch.io (com modelo pague o quanto quiser)",
                    "Apenas na Google Play Store",
                    "Apenas enviando por e-mail para cada jogador"
                ],
                "correct_index": 1
            },
            {
                "id": 3,
                "question": "Segundo o guia de marketing da plataforma, qual é a meta ideal de jogadores orgânicos iniciais para focar na divulgação?",
                "options": [
                    "Os primeiros 100 jogadores",
                    "Os primeiros 10.000 jogadores",
                    "Mais de 1 milhão de jogadores no primeiro dia",
                    "Apenas amigos e familiares"
                ],
                "correct_index": 1
            }
        ]
    
    return [
        {
            "id": 1,
            "question": "O que é um 'Behavior' (Comportamento) na GDevelop?",
            "options": [
                "Uma regra de conduta para o jogador",
                "Uma funcionalidade pré-programada nativa que adiciona mecânicas prontas ao objeto",
                "Um script escrito em JavaScript para rodar no navegador",
                "Um tipo de variável global"
            ],
            "correct_index": 1
        },
        {
            "id": 2,
            "question": "Como funcionam as Condições e Ações na folha de eventos da GDevelop?",
            "options": [
                "As Ações rodam primeiro e depois testam as Condições",
                "Condições e Ações rodam de forma aleatória",
                "Se as Condições forem verdadeiras, as Ações correspondentes serão executadas",
                "As Condições mudam a tela e as Ações salvam dados"
            ],
            "correct_index": 2
        },
        {
            "id": 3,
            "question": "Qual recurso da GDevelop é ideal para fazer interpolações suaves de posição, escala, ângulo ou opacidade de objetos?",
            "options": [
                "Tween (Interpolação)",
                "Anchor (Ancoragem)",
                "Pathfinding (Busca de caminhos)",
                "Platformer Character"
            ],
            "correct_index": 0
        }
    ]


def generate_quiz_for_module(module):
    """Generate 3 multiple-choice questions for a module using Gemini, or fall back to default questions."""
    import os
    import json
    from google import genai

    gemini_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_key:
        return get_fallback_quiz(module)

    # Compile lesson titles for context
    lessons_titles = [l.title for l in module.published_lessons.all()]
    lessons_context = ", ".join(lessons_titles) if lessons_titles else "Nenhuma aula listada"

    prompt = f"""Crie um quiz de exatamente 3 perguntas de múltipla escolha baseadas nas seguintes informações sobre o módulo do curso de desenvolvimento de jogos:
Módulo: {module.title}
Descrição: {module.description}
Aulas: {lessons_context}

O quiz deve ser focado estritamente na engine GDevelop e em desenvolvimento de jogos sem código (No-Code), compatível com o tema do módulo. Cada pergunta deve ter exatamente 4 opções de resposta e indicar o index da resposta correta (0 para a primeira, 1 para a segunda, etc.).
Responda APENAS com um objeto JSON válido no seguinte formato:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Texto da pergunta?",
      "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "correct_index": 0
    }},
    {{
      "id": 2,
      "question": "Texto da segunda pergunta?",
      "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "correct_index": 2
    }},
    {{
      "id": 3,
      "question": "Texto da terceira pergunta?",
      "options": ["Opção A", "Opção B", "Opção C", "Opção D"],
      "correct_index": 1
    }}
  ]
}}
Retorne apenas o JSON limpo, sem blocos de código markdown ou texto extra.
"""
    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        
        # Clean response text
        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:]
        if resp_text.endswith("```"):
            resp_text = resp_text[:-3]
        resp_text = resp_text.strip()
        
        data = json.loads(resp_text)
        if "questions" in data and len(data["questions"]) == 3:
            return data["questions"]
    except Exception as e:
        print(f"[GDev Quiz] Gemini generation failed, using fallback: {e}")
        
    return get_fallback_quiz(module)


@main_bp.route('/course/module/<int:module_id>/quiz')
@login_required
def module_quiz(module_id):
    """Start or view the quiz for a completed module."""
    module = Module.query.get_or_404(module_id)
    if not module.is_published:
        abort(404)

    # Check if user completed all lessons in the module
    if not current_user.has_completed_all_lessons(module):
        flash('Você precisa concluir todas as aulas do módulo antes de realizar o quiz!', 'warning')
        return redirect(url_for('main.module_detail', module_id=module_id))

    # Retrieve or generate the quiz questions
    active_quiz = session.get('active_quiz')
    if active_quiz and active_quiz.get('module_id') == module_id:
        questions = active_quiz.get('questions')
    else:
        questions = generate_quiz_for_module(module)
        session['active_quiz'] = {
            'module_id': module_id,
            'questions': questions
        }

    return render_template('course/quiz.html', module=module, questions=questions)


@main_bp.route('/course/module/<int:module_id>/quiz/submit', methods=['POST'])
@login_required
def submit_module_quiz(module_id):
    """Submit quiz answers and evaluate the score."""
    module = Module.query.get_or_404(module_id)
    if not module.is_published:
        abort(404)

    if not current_user.has_completed_all_lessons(module):
        flash('Você precisa concluir todas as aulas antes de enviar as respostas do quiz!', 'warning')
        return redirect(url_for('main.module_detail', module_id=module_id))

    active_quiz = session.get('active_quiz')
    if not active_quiz or active_quiz.get('module_id') != module_id:
        flash('Sessão de quiz inválida. Por favor, tente novamente.', 'warning')
        return redirect(url_for('main.module_quiz', module_id=module_id))

    questions = active_quiz['questions']
    score = 0

    # Evaluate answers
    for q in questions:
        selected_option = request.form.get(f"question_{q['id']}")
        if selected_option is not None:
            if int(selected_option) == q['correct_index']:
                score += 1

    passed = score >= 2

    if passed:
        completion = ModuleQuizCompletion.query.filter_by(user_id=current_user.id, module_id=module_id).first()
        if not completion:
            completion = ModuleQuizCompletion(
                user_id=current_user.id,
                module_id=module_id,
                score=score,
                completed=True
            )
            db.session.add(completion)
        else:
            completion.score = score
            completion.completed = True
            completion.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('Parabéns! Você passou no quiz e completou o módulo.', 'success')
    else:
        flash('Você não obteve a pontuação mínima necessária. Tente novamente!', 'danger')

    next_module = Module.query.filter(
        Module.is_published == True,
        Module.order > module.order
    ).order_by(Module.order).first()

    session.pop('active_quiz', None)

    return render_template('course/quiz_result.html', module=module, score=score, passed=passed, next_module=next_module)


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
    """API endpoint for Gemini-powered helper chatbot."""
    import os
    from google import genai
    from flask import jsonify

    # Get user message
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"response": "Por favor, envie uma mensagem válida."}), 400

    # Get Gemini API key from Railway env
    gemini_key = os.environ.get('GEMINI_API_KEY')

    if not gemini_key:
        return jsonify({
            "response": "Olá! Eu sou o GDev Helper. No momento, minha chave de acesso à inteligência artificial não está configurada no servidor. Por favor, avise o administrador do site para cadastrar a variável GEMINI_API_KEY!"
        }), 200

    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=gemini_key)

        # Query active modules and lessons dynamically from database
        try:
            from app.models import Module, Lesson
            published_modules = Module.query.filter_by(is_published=True).order_by(Module.order).all()
            if published_modules:
                modules_list = []
                for mod in published_modules:
                    lessons_list = []
                    # Fetch published lessons for this module
                    pub_lessons = mod.published_lessons.all()
                    for idx, les in enumerate(pub_lessons, 1):
                        lessons_list.append(f"    - Aula {idx}: {les.title} ({les.duration_minutes} min)")
                    lessons_str = "\n".join(lessons_list) if lessons_list else "    - (Nenhuma aula publicada neste módulo)"
                    modules_list.append(
                        f"  * Módulo {mod.order + 1}: {mod.title}\n"
                        f"    Descrição: {mod.description}\n"
                        f"    Aulas:\n{lessons_str}"
                    )
                course_structure = "\n" + "\n\n".join(modules_list)
            else:
                course_structure = "\n  (Nenhum módulo publicado no momento)"
        except Exception as e:
            print(f"[GDev Helper] Error querying DB models: {e}")
            course_structure = "\n  (Erro ao obter lista de módulos do banco de dados)"

        # System prompt based on official guidelines for gdevtutorial.online and GDevelop-specific accuracy
        system_prompt = f"""You are the official AI Assistant for "gdevtutorial.online", an online academy specialized in free, open-source, no-code game development using the GDevelop engine.
Your primary mission is to guide users through tutorials, extensions, monetization strategies, and game-feel optimization based strictly on the content of the platform.

CRITICAL INSTRUCTIONS:
1. FOCUS ON GDEVELOP EVENT SHEET STRUCTURE: All programming logic must be described in GDevelop visual terms (Events, Conditions, Actions, Behaviors). Never suggest pure code (like JavaScript/C#) unless explicitly asked. The engine uses a visual condition/action model, and your responses must reflect this visual layout.
2. ACCURACY: Be extremely coherent with GDevelop's features:
   - Refer to Behaviors by their exact GDevelop names: "Platformer Character" (Objeto de plataforma), "Platform" (Plataforma), "Pathfinding", "Tween", "Physics 2.0", "Anchor", "Top-down Movement", "Draggable".
   - Events are structured as: Condições (Conditions) on the left side, Ações (Actions) on the right side.
   - Expressions/Formulas: Use GDevelop syntax like: `Object.X()`, `Object.Y()`, `Variable(myVar)`, `GlobalVarString(myVar)`, `RandomInRange(min, max)`.
3. CONCISENESS & COMPLETENESS: Ensure your response is highly informative but straight to the point. Avoid long conversational greetings, repetitive explanations, or filler words. Give complete answers so they never get truncated. Go straight to explaining GDevelop logic, using clean bulleted steps.
4. OUT OF SCOPE: If asked about general topics or unrelated software (or other game engines like Unity, Godot, Unreal), politely steer the conversation back to game development in GDevelop. Use the friendly decline message if it's completely unrelated: "Eu fui treinado para ajudar exclusivamente com os tutoriais, ferramentas e estratégias de desenvolvimento de jogos do gdevtutorial.online. Como posso ajudar no seu projeto de jogo hoje?"
5. SOURCE REINFORCEMENT: Frequently remind users that complete video guides, asset bundles, and templates are available directly on the gdevtutorial.online platform.
6. CONTENT MAPPING MATRIX:
   - Criar primeiro jogo / aprender interface -> Guide them to "Guia Iniciante: Do Zero ao Criador" (Explain Events/Actions logic & templates).
   - Movimentação inteligente ou física -> Guide to "Extensões de Pathfinding / Physics" (Explain native behaviors without code).
   - Salvar progresso de múltiplos objetos -> Guide to "Tutorial de Estrutura de Arrays e Memória" (Explain saving X, Y, and names in arrays).
   - Ganhar dinheiro ou publicar o jogo -> Guide to "Módulo de Monetização e Marketing" (List 4 monetization methods: Ads, In-App Purchases, Web Premium/Donations, Steam/Epic Games, and 5 marketing strategies for first 10k players).

DYNAMIC COURSE CONTENT (DATABASE CONTEXT):
Use the list below to accurately reply whenever a user asks about modules, lessons, course contents, available courses, what they will learn, or similar queries. Do not make up modules or lessons that are not listed here:
{course_structure}

LANGUAGE: Always reply in the same language the user speaks to you (Default to Portuguese if they start in Portuguese).

SYSTEM ARCHITECTURE FOR SOLUTIONS:
When providing tutorial logic or explaining how to build a mechanic, structure your response strictly with:
- **Mecânica**: Brief description of the mechanic and why it matters.
- **Preparação**: Objects or Behaviors/Extensions needed on the scene.
- **Eventos**:
  * [CONDIÇÃO] -> What triggers the event.
  * [AÇÃO] -> What happens.
- **Dica de Juice**: A small tip to improve the game feel/juice (screenshake, particles, dynamic feedback).

FEW-SHOT EXAMPLES:

Exemplo 1 — Entrada do Usuário:
"Como eu faço para o meu inimigo seguir o jogador pela tela?"
Resposta Esperada:
No gdevtutorial.online, ensinamos a resolver isso de forma simples usando o comportamento de Pathfinding (Busca de Caminhos), sem programar nenhuma linha de código!
- **Mecânica**: Movimentação inteligente de inimigos para seguir o jogador desviando de obstáculos.
- **Preparação**: Adicione o comportamento (Behavior) de Pathfinding ao objeto do seu Inimigo. Garanta que os seus obstáculos tenham o comportamento de Pathfinding Obstacle.
- **Eventos**:
  * [CONDIÇÃO]: Sempre (ou De tempo em tempo, ex: a cada 0.2 segundos)
  * [AÇÃO]: Escolha o objeto Inimigo -> Mover para uma posição usando Pathfinding -> Defina o destino como Jogador.X() e Jogador.Y().
- **Dica de Juice**: Para deixar o jogo mais dinâmico, mude a animação do seu inimigo para "Correndo" assim que a velocidade dele for maior que 0!

Exemplo 2 — Entrada do Usuário:
"Como posso ganhar dinheiro com o meu jogo criado na GDevelop?"
Resposta Esperada:
Excelente pergunta! No módulo de negócios do gdevtutorial.online, destacamos 4 formas principais e diretas para monetizar seus jogos:
1. Anúncios Integrados (Mobile/Web): Utilizando redes como AdMob para exibir recompensas em vídeo ou banners.
2. Compras no Aplicativo (In-App Purchases): Venda de itens cosméticos, moedas do jogo ou remoção de anúncios.
3. Plataformas Web Premium/Doações: Publicar em portais como Itch.io com o modelo "Pague o quanto quiser" ou Newgrounds.
4. Publicação Comercial (Steam / Epic Games): Empacotar o jogo para PC e vendê-lo como um produto premium.
Para atrair público para essas opções, lembre-se de seguir o nosso guia de marketing focado em conseguir os primeiros 10.000 jogadores orgânicos através de comunidades e redes sociais.
"""

        # Make request to Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=3000,
                temperature=0.7,
            ),
        )

        # Extract text response from Gemini
        ai_response = response.text.strip()
        return jsonify({"response": ai_response})

    except Exception as e:
        error_msg = str(e).lower()
        if 'api key' in error_msg or 'authentication' in error_msg or '401' in error_msg or '403' in error_msg:
            print(f"[GDev Helper] Gemini API Authentication Error: {e}")
            return jsonify({
                "response": "Olá! A chave de API do Gemini parece estar inválida. Por favor, avise o administrador para verificar a variável GEMINI_API_KEY no servidor."
            }), 200
        elif 'rate' in error_msg or '429' in error_msg:
            print(f"[GDev Helper] Gemini API Rate Limit Error: {e}")
            return jsonify({
                "response": "Estou recebendo muitas perguntas no momento! 😅 Por favor, tente novamente em alguns segundos."
            }), 200
        else:
            print(f"[GDev Helper] Chat Exception: {e}")
            return jsonify({
                "response": "Ops! Ocorreu um erro de conexão com o cérebro da inteligência artificial. Por favor, tente novamente."
            }), 200

