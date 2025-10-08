import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from extensions import db, socketio
from config import ProductionConfig, DevelopmentConfig

load_dotenv()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration depending on environment
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Allow overriding with env vars
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))

    # Ensure instance folder exists (SQLite file will live here by default)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass

    # Default upload folder if not configured
    app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.instance_path, 'uploads'))

    # Initialize extensions
    db.init_app(app)

    # Optional message queue (Redis) for Socket.IO when scaling
    redis_url = os.getenv('REDIS_URL')
    socketio_kwargs = {'cors_allowed_origins': '*'}
    if redis_url:
        socketio_kwargs['message_queue'] = redis_url

    socketio.init_app(app, **socketio_kwargs)

    # Respect reverse proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Register blueprints and other runtime setup
    with app.app_context():
        # Import models to ensure tables are created
        try:
            from models.user import User, Group, user_groups
        except Exception:
            # models.user may not define Groups in simpler projects — ignore if missing
            pass
        from models.message import Message

        # Blueprints
        from routes.chat import bp as chat_bp, init_socket_handlers
        app.register_blueprint(chat_bp)

        # Additional blueprints (optional)
        try:
            from routes.upload import bp_upload
            app.register_blueprint(bp_upload)
        except Exception:
            pass

        try:
            from routes.auth import bp_auth
            app.register_blueprint(bp_auth)
        except Exception:
            pass

        try:
            from routes.groups import bp_groups
            app.register_blueprint(bp_groups)
        except Exception:
            pass

        # Register socket handlers
        init_socket_handlers(socketio, db)

        # Create tables and upload folder
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app


app = create_app()

# Health check endpoint (useful for deploy probes)
@app.route('/health')
def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    # Diagnostic: print registered routes when running locally in debug
    if app.config.get('DEBUG', True):
        print('\nRegistered routes:')
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"{rule.rule:30s} -> {rule.endpoint:30s} [{methods}]")

    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config.get('DEBUG', True)
    )