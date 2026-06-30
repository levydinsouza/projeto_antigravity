from datetime import datetime, timezone
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    """User model for authentication and profile."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    profile_pic_url = db.Column(db.String(500), default='')
    profile_pic_public_id = db.Column(db.String(300), default='')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    progress = db.relationship('UserProgress', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')
    quiz_completions = db.relationship('ModuleQuizCompletion', backref='user', lazy='dynamic',
                                       cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def completed_lessons_count(self):
        return self.progress.filter_by(completed=True).count()

    def get_progress_for_lesson(self, lesson_id):
        return self.progress.filter_by(lesson_id=lesson_id).first()

    def has_completed_lesson(self, lesson_id):
        prog = self.get_progress_for_lesson(lesson_id)
        return prog is not None and prog.completed

    def has_completed_all_lessons(self, module):
        """Check if user completed all published lessons in a module."""
        pub_lessons = module.published_lessons.all()
        if not pub_lessons:
            return False
        for lesson in pub_lessons:
            if not self.has_completed_lesson(lesson.id):
                return False
        return True

    def get_quiz_completion(self, module_id):
        """Get quiz completion record for a module."""
        return self.quiz_completions.filter_by(module_id=module_id).first()

    def has_completed_quiz(self, module_id):
        """Check if user successfully passed the quiz for a module."""
        completion = self.get_quiz_completion(module_id)
        return completion is not None and completion.completed

    def has_completed_all_required_courses(self):
        """Check if user has passed the quiz for every required (non-optional) published module."""
        required_modules = Module.query.filter_by(is_published=True, is_optional=False).all()
        if not required_modules:
            return False
        for module in required_modules:
            if not self.has_completed_quiz(module.id):
                return False
        return True


class Module(db.Model):
    """Course module/section."""
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    thumbnail_url = db.Column(db.String(500), default='')
    thumbnail_public_id = db.Column(db.String(300), default='')
    order = db.Column(db.Integer, default=0, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_optional = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    lessons = db.relationship('Lesson', backref='module', lazy='dynamic',
                              cascade='all, delete-orphan',
                              order_by='Lesson.order')

    def __repr__(self):
        return f'<Module {self.title}>'

    @property
    def lessons_count(self):
        return self.lessons.count()

    @property
    def published_lessons(self):
        return self.lessons.filter_by(is_published=True).order_by(Lesson.order)

    @property
    def total_duration(self):
        result = db.session.query(
            db.func.sum(Lesson.duration_minutes)
        ).filter(
            Lesson.module_id == self.id,
            Lesson.is_published == True
        ).scalar()
        return result or 0


class Lesson(db.Model):
    """Individual lesson/video within a module."""
    __tablename__ = 'lessons'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    video_url = db.Column(db.String(500), default='')
    content = db.Column(db.Text, default='')
    order = db.Column(db.Integer, default=0, nullable=False)
    duration_minutes = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    pdf_url = db.Column(db.String(500), default='')
    pdf_public_id = db.Column(db.String(300), default='')
    html_url = db.Column(db.String(500), default='')
    html_public_id = db.Column(db.String(300), default='')

    # Relationships
    progress = db.relationship('UserProgress', backref='lesson', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Lesson {self.title}>'

    @property
    def embed_url(self):
        """Convert YouTube/Vimeo URL to embed format."""
        url = self.video_url or ''

        # YouTube
        if 'youtube.com/watch' in url:
            video_id = url.split('v=')[1].split('&')[0] if 'v=' in url else ''
            return f'https://www.youtube.com/embed/{video_id}' if video_id else ''
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f'https://www.youtube.com/embed/{video_id}' if video_id else ''
        elif 'youtube.com/embed/' in url:
            return url

        # Vimeo
        if 'vimeo.com/' in url and 'player.vimeo.com' not in url:
            video_id = url.split('vimeo.com/')[1].split('?')[0]
            return f'https://player.vimeo.com/video/{video_id}' if video_id else ''
        elif 'player.vimeo.com' in url:
            return url

        return url


class UserProgress(db.Model):
    """Track user progress through lessons."""
    __tablename__ = 'user_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False, index=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Unique constraint: one progress record per user per lesson
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson'),
    )

    def __repr__(self):
        return f'<UserProgress user={self.user_id} lesson={self.lesson_id}>'


class ModuleQuizCompletion(db.Model):
    """Track module quiz completion/confirmation."""
    __tablename__ = 'module_quiz_completions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False, index=True)
    completed = db.Column(db.Boolean, default=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Unique constraint: one quiz completion per user per module
    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_id', name='uq_user_module_quiz'),
    )

    def __repr__(self):
        return f'<ModuleQuizCompletion user={self.user_id} module={self.module_id} score={self.score}>'

