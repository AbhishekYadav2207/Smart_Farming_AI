import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import urllib.parse

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'e16221919a79e74e0b1f5cee866667991ec26d0aeb3568a4fc7b250db98a6cc5')
    # PostgreSQL configuration for Render
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # Session expires after 30 minutes
    SESSION_REFRESH_EACH_REQUEST = True  # Reset the session timeout on each request
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF attacks

