"""
Configuration settings for the CRS Rice Bowl application.
"""
import os
from pathlib import Path


class Config:
    """Application configuration class."""

    # Base directory
    BASE_DIR = Path(__file__).parent.parent

    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lent-2026-crs-rice-bowl-secret-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "data" / "crs.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

    # Flask-Login configuration
    REMEMBER_COOKIE_DURATION = 86400  # 24 hours
    SESSION_PROTECTION = 'strong'
