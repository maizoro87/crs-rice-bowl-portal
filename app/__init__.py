"""
Flask application factory for CRS Rice Bowl application.
"""
import os
from pathlib import Path
from flask import Flask, send_from_directory
from flask_login import LoginManager
from app.config import Config
from app.models import db, User


def create_app(config_class=Config) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application instance
    """
    # Set up static folder to serve public files
    base_dir = Path(__file__).resolve().parent.parent
    public_dir = base_dir / 'public'

    app = Flask(__name__, static_folder=str(public_dir), static_url_path='')
    app.config.from_object(config_class)

    # Ensure data directory exists
    data_dir = Path(app.config['BASE_DIR']) / 'data'
    data_dir.mkdir(exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin_bp.login'
    login_manager.login_message = 'Please log in to access the admin panel.'

    @login_manager.user_loader
    def load_user(user_id: str) -> User:
        """
        Load user by ID for Flask-Login.

        Args:
            user_id: User ID to load

        Returns:
            User instance or None
        """
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Serve index.html at root
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    # Initialize database and create default admin user
    with app.app_context():
        db.create_all()
        _create_default_admin()

    return app


def _create_default_admin() -> None:
    """
    Create default admin user if no users exist in the database.
    Default credentials: username='admin', password='lent2026'
    """
    if User.query.count() == 0:
        admin_user = User(username='admin')
        admin_user.set_password('lent2026')
        db.session.add(admin_user)
        db.session.commit()
        print('Created default admin user (username: admin, password: lent2026)')
