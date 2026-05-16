# app/config.py
import os
from pathlib import Path

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Default to SQLite for local dev if DATABASE_URL not set
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    # Railway provides DATABASE_URL with postgres://, SQLAlchemy expects postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

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
