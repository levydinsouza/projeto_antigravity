# app/config.py
import os
from pathlib import Path

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Default to SQLite for local dev if DATABASE_URL not set or empty
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = 'sqlite:///dev.db'
    elif db_url.startswith('postgres://'):
        # Railway provides DATABASE_URL with postgres://, SQLAlchemy expects postgresql://
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = db_url

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'

# Helper to select config based on FLASK_ENV env var
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
