import os
import logging
from config import ProductionConfig

class RenderProductionConfig(ProductionConfig):
    """Конфигурация для Render.com"""
    
    # Настройки базы данных
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Логирование
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настройки WebSocket
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Безопасность
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Загрузка файлов
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Логирование в stdout для Render
        import logging
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

def get_production_config():
    return RenderProductionConfig