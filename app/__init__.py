import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('app.config.Config')

    # Safe database connection logging in startup logs
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite'):
        print("[GDev] DB CONFIG: Running on SQLite (ephemeral). WARNING: Data will be lost on deploy!")
    else:
        # Hide credentials for safety
        safe_uri = db_uri.split('@')[-1] if '@' in db_uri else db_uri
        print(f"[GDev] DB CONFIG: Connected to PostgreSQL at {safe_uri}")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register Jinja2 filters
    @app.template_filter('linkify')
    def linkify(text):
        import re
        from markupsafe import Markup
        if not text:
            return ""
        url_pattern = re.compile(r'((?:https?://|www\.)[^\s<>\'\"]+)')
        def replace(match):
            url = match.group(0)
            href = url
            if url.startswith('www.'):
                href = 'https://' + url
            return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{url}</a>'
        escaped = Markup.escape(text)
        linkified = url_pattern.sub(replace, escaped)
        formatted = linkified.replace('\n', Markup('<br>'))
        return Markup(formatted)

    @app.template_filter('download_url')
    def download_url(url):
        if not url:
            return ""
        if "/upload/" in url:
            return url.replace("/upload/", "/upload/fl_attachment/", 1)
        return url

    @app.template_filter('pdf_thumbnail')
    def pdf_thumbnail(url):
        if not url:
            return ""
        if "/image/upload/" in url:
            base_url = url
            if base_url.lower().endswith('.pdf'):
                base_url = base_url[:-4] + '.jpg'
            return base_url.replace("/image/upload/", "/image/upload/pg_1,w_300,h_400,c_fill/", 1)
        return ""

    # Import models so Alembic can detect the schema
    from app import models

    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    # User loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin_panel import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Initialize Cloudinary for image uploads
    from app.cloudinary_utils import init_cloudinary
    init_cloudinary(app)

    # Seed admin user (tables are managed by Alembic via 'flask db upgrade')
    with app.app_context():
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create default admin user if not exists."""
    from app.models import User
    from werkzeug.security import generate_password_hash
    from sqlalchemy.exc import ProgrammingError, OperationalError

    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@gdevtutorial.com')
    
    try:
        admin = User.query.filter_by(email=admin_email).first()
    except (ProgrammingError, OperationalError):
        # Database tables might not exist yet
        return

    if not admin:
        admin = User(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            email=admin_email,
            password_hash=generate_password_hash(
                os.environ.get('ADMIN_PASSWORD', 'admin123')
            ),
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f'[GDev] Admin user created: {admin_email}')
