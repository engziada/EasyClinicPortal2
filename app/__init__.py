"""
Easy Clinic Portal - A Flask-based web portal for a dermatology clinic.
This module initializes the Flask application and its extensions.
"""
import os
from flask import Flask, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=None):
    """
    Create and configure the Flask application.

    Args:
        config_class: Configuration class to use.

    Returns:
        Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_pyfile('../config.py')

    # Ensure the upload directory exists
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'images'), exist_ok=True)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Set up login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.patients.routes import patients_bp
    from app.doctors.routes import doctors_bp
    from app.assistants.routes import assistants_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(assistants_bp)
    app.register_blueprint(admin_bp)

    # Add main route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Register global error handlers
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_):
        flash('CSRF token validation failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    # Register error handlers

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create a superadmin user if it doesn't exist
        from app.models.user import User, Role
        from werkzeug.security import generate_password_hash

        superadmin = User.query.filter_by(email='admin@easyclinic.com').first()
        if not superadmin:
            superadmin = User(
                name='Super Admin',
                email='admin@easyclinic.com',
                password='admin123',  # This will be hashed by the password setter
                role=Role.SUPERADMIN
            )
            db.session.add(superadmin)
            db.session.commit()
        else:
            # Update the admin password to ensure it works
            superadmin.password = 'admin123'  # This will be hashed by the password setter
            db.session.commit()

    return app
