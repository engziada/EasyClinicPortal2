"""
Configuration settings for Easy Clinic Portal.
"""
import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Secret key for session management
SECRET_KEY = os.urandom(24).hex()

# CSRF Protection
WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = os.urandom(24).hex()

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Upload configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Session configuration
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Debug mode
DEBUG = True
