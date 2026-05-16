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

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

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

    # Create tables and seed admin user
    with app.app_context():
        # db.create_all() is removed in favor of Flask-Migrate
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
        # Database tables might not exist yet (before migrations)
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
