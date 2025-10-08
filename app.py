import os
from flask import Flask, redirect, jsonify, session, request
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from extensions import db, socketio
from config import ProductionConfig, DevelopmentConfig

load_dotenv()


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
        template_folder="templates",
        instance_relative_config=True,
    )

    # --- Конфигурация окружения ---
    env = os.getenv("FLASK_ENV", "development").lower()
    config_class = ProductionConfig if env == "production" else DevelopmentConfig
    app.config.from_object(config_class)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", app.config.get("SECRET_KEY")),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", app.config.get("SQLALCHEMY_DATABASE_URI")
        ),
        # Настройки сессии для безопасности
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=env == "production",
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=86400,  # 24 часа
    )

    # --- Каталоги ---
    os.makedirs(app.instance_path, exist_ok=True)
    upload_path = os.path.join(app.instance_path, "uploads")
    os.makedirs(upload_path, exist_ok=True)
    app.config.setdefault("UPLOAD_FOLDER", upload_path)

    # --- Инициализация расширений ---
    db.init_app(app)

    redis_url = os.getenv("REDIS_URL")
    socketio_kwargs = {
        "cors_allowed_origins": "*",
        "async_mode": "eventlet" if env == "production" else None,
    }
    if redis_url:
        socketio_kwargs["message_queue"] = redis_url

    socketio.init_app(app, **socketio_kwargs)

    # --- ProxyFix для работы за обратным прокси (Render/Nginx/Cloudflare) ---
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # --- Регистрация моделей и blueprint'ов ---
    with app.app_context():
        # Модели
        from models.message import Message
        try:
            from models.user import User, Group, user_groups
        except ImportError as e:
            if app.config.get("DEBUG"):
                print(f"⚠️ Models import warning: {e}")

        # Blueprints
        from routes.chat import bp as chat_bp, init_socket_handlers
        app.register_blueprint(chat_bp)

        for route_path, bp_name in [
            ("routes.upload", "bp_upload"),
            ("routes.auth", "bp_auth"),
            ("routes.groups", "bp_groups"),
        ]:
            try:
                module = __import__(route_path, fromlist=[bp_name])
                app.register_blueprint(getattr(module, bp_name))
                if app.config.get("DEBUG"):
                    print(f"✅ Registered blueprint: {route_path}.{bp_name}")
            except ImportError as e:
                if app.config.get("DEBUG"):
                    print(f"⚠️ Blueprint not found: {route_path}.{bp_name} - {e}")

        # Инициализация socket.io обработчиков
        init_socket_handlers(socketio, db)

        # --- Создание БД только в режиме разработки ---
        if app.config.get("DEBUG", False):
            db.create_all()
            if app.config.get("DEBUG"):
                print("✅ Database tables created")

    return app


app = create_app()


@app.before_request
def check_authentication():
    """Проверяем аутентификацию для защищенных маршрутов"""
    current_path = request.path
    
    # Всегда разрешаем доступ к этим маршрутам
    if (current_path.startswith('/static/') or
        current_path in ['/', '/health', '/api/user/check'] or
        current_path.startswith('/auth/')):
        return
    
    # Проверяем авторизацию для защищенных маршрутов
    if (current_path.startswith('/chat/') or 
        current_path == '/chat' or
        (current_path.startswith('/api/') and not current_path == '/api/user/check')):
        
        user_uuid = session.get('user_uuid')
        if not user_uuid:
            return redirect('/auth/')


@app.route("/")
def index():
    """Главная страница - редирект на логин"""
    return redirect("/auth/")


@app.route("/health")
def health():
    """Health check для мониторинга"""
    return jsonify({
        "status": "ok", 
        "environment": os.getenv("FLASK_ENV", "development"),
        "debug": app.config.get("DEBUG", False)
    })


@app.route("/api/user/check")
def check_user_session():
    """Проверка активной сессии пользователя"""
    user_uuid = session.get('user_uuid')
    if user_uuid:
        try:
            from models.user import User
            user = User.query.filter_by(uuid=user_uuid).first()
            if user:
                return jsonify({
                    "authenticated": True, 
                    "user": user.to_dict()
                })
        except Exception as e:
            if app.config.get("DEBUG"):
                print(f"Error checking user session: {e}")
    
    return jsonify({"authenticated": False})


if __name__ == "__main__":
    debug_mode = app.config.get("DEBUG", True)
    port = int(os.getenv("PORT", 5000))

    if debug_mode:
        print("\n" + "="*50)
        print("🚀 FLASK CHAT APPLICATION")
        print("="*50)
        
        print("\n✅ Registered routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            print(f"  {rule.rule:30s} → {rule.endpoint:30s} [{methods}]")

        print(f"\n📊 Server Info:")
        print(f"  Environment: {os.getenv('FLASK_ENV', 'development')}")
        print(f"  Debug mode: {debug_mode}")
        print(f"  Port: {port}")
        print(f"  Host: {'127.0.0.1' if debug_mode else '0.0.0.0'}")
        print(f"  Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Unknown')}")
        
        print(f"\n🔐 Authentication:")
        print(f"  Protected routes: /chat/, /api/")
        print(f"  Login page: /auth/")
        print(f"  Session check: /api/user/check")
        
        print(f"\n🌐 Starting server at: http://127.0.0.1:{port}")
        print("="*50 + "\n")

    socketio.run(
        app,
        host="127.0.0.1" if debug_mode else "0.0.0.0",
        port=port,
        debug=debug_mode,
        allow_unsafe_werkzeug=True,
    )