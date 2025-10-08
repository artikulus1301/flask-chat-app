import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Основная конфигурация приложения"""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/chat.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 МБ
    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "mp4", "pdf", "zip", "txt",
        "webp", "mp3", "wav", "doc", "docx"
    }
    
    SOCKETIO_ASYNC_MODE = "eventlet"
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    CRYPTO_ALGORITHM = "fernet"
    E2E_ENABLED = True
    
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    
    MAX_GROUP_MEMBERS = 50
    DEFAULT_GROUP_NAME = "Общий чат"
    
    MESSAGE_HISTORY_LIMIT = 1000
    MESSAGE_MAX_LENGTH = 2000

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    TESTING = False
    
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    if os.getenv("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)
    # Security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Получить конфигурацию на основе переменной окружения FLASK_ENV"""
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_dict.get(env, config_dict['default'])