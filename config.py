"""
Configuration settings for the Active Directory Clone application.
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ad_clone.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_PROTECTION = 'strong'
    
    # Password policy settings
    MIN_PASSWORD_LENGTH = 8
    MAX_FAILED_ATTEMPTS = 3
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=15)
    
    # Application settings
    ITEMS_PER_PAGE = 20
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}