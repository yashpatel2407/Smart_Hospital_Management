import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-care-hospital-secret-key-2024')
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'smartcare_hospital')
    MYSQL_CURSORCLASS = 'DictCursor'
    MYSQL_AUTOCOMMIT = True
    
    # Auto-reconnect to handle "Server has gone away" errors
    MYSQL_CUSTOM_OPTIONS = {"connect_timeout": 5}
    
    # OpenAI API Key for Medical Chatbot
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    
    # Flask-Mail Configuration - OTP Email System
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', '')