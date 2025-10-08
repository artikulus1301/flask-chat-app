"""
debugger.py — расширенный дебаггер Flask + SocketIO + SQLAlchemy
Позволяет отслеживать запросы, события, ошибки и состояние БД.
"""

import logging
import time
from flask import request
from app import db, socketio

# === НАСТРОЙКА ЛОГГЕРА ===
logger = logging.getLogger("FlaskDebugger")
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s",
    "%Y-%m-%d %H:%M:%S"
))
logger.addHandler(console)


# === ЛОГИРОВАНИЕ HTTP-ЗАПРОСОВ ===
def init_request_debugger(app):
    """Перехватывает каждый запрос и выводит его параметры в консоль"""

    @app.before_request
    def before_request():
        request.start_time = time.time()
        logger.debug(f"➡️  {request.method} {request.path} — args={dict(request.args)} json={request.get_json(silent=True)}")

    @app.after_request
    def after_request(response):
        duration = time.time() - getattr(request, 'start_time', time.time())
        logger.debug(f"⬅️  {response.status} ({duration:.3f}s) — {request.path}")
        return response

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            logger.error(f"🔥 Exception during request: {exception}")


# === ЛОГИРОВАНИЕ СОБЫТИЙ SOCKET.IO ===
def init_socket_debugger(socketio):
    """Перехватывает события Socket.IO"""
    @socketio.on('connect')
    def on_connect():
        logger.info(f"🟢 Socket connected: {request.sid}")

    @socketio.on('disconnect')
    def on_disconnect():
        logger.info(f"🔴 Socket disconnected: {request.sid}")

    @socketio.on_error()
    def on_error(e):
        logger.error(f"⚠️ SocketIO error: {e}")


# === ЛОГИРОВАНИЕ SQLAlchemy ===
def init_db_debugger(app):
    """Включает подробный SQL-лог"""
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').addHandler(console)
    logger.info("🧩 SQLAlchemy query logging enabled")


# === ГЛАВНАЯ ТОЧКА ИНИЦИАЛИЗАЦИИ ===
def init_debugger(app):
    """Активирует все дебаг-функции"""
    init_request_debugger(app)
    init_db_debugger(app)
    init_socket_debugger(socketio)
    logger.info("✅ Flask Debugger initialized successfully!")
