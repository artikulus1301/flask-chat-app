import os
from dotenv import load_dotenv

# --- Загружаем переменные окружения ---
load_dotenv()


class Config:
    """Базовая конфигурация приложения (общая для всех окружений)."""

    # --- Безопасность ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # --- База данных ---
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///instance/chat.db"
    ).replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Загрузка файлов ---
    INSTANCE_FOLDER = os.path.join(os.getcwd(), "instance")
    UPLOAD_FOLDER = os.path.join(INSTANCE_FOLDER, "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 МБ

    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "mp4", "pdf", "zip", "txt",
        "webp", "mp3", "wav", "doc", "docx"
    }

    # --- SocketIO ---
    SOCKETIO_ASYNC_MODE = "eventlet"  # подходит для продакшена
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

    # --- Шифрование сообщений ---
    CRYPTO_ALGORITHM = "fernet"
    E2E_ENABLED = True  # флаг для включения end-to-end шифрования

    # --- Облачное хранилище (опционально) ---
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    # --- Ограничения и параметры чата ---
    MAX_GROUP_MEMBERS = 50
    DEFAULT_GROUP_NAME = "Общий чат"
    MESSAGE_HISTORY_LIMIT = 1000
    MESSAGE_MAX_LENGTH = 2000


# --- Конфигурации окружений ---
class DevelopmentConfig(Config):
    """Конфигурация для локальной разработки."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Конфигурация для боевого окружения."""
    DEBUG = False
    TESTING = False

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///instance/chat.db"
    ).replace("postgres://", "postgresql://", 1)

    # Безопасные cookie для HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Режим продакшена для Render / Docker
    PREFERRED_URL_SCHEME = "https"


class TestingConfig(Config):
    """Конфигурация для unit-тестов."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# --- Выбор конфигурации по окружению ---
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Возвращает активную конфигурацию на основе FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_dict.get(env, config_dict["default"])
