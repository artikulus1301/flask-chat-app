from flask import Flask
from flask_socketio import SocketIO
import os

from extensions import db, socketio

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///chat.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    with app.app_context():
        from routes.chat import bp as chat_bp
        app.register_blueprint(chat_bp)
        # Ensure socket event handlers are registered so the server
        # responds to `user_join` and `message` events from clients.
        from routes.chat import init_socket_handlers
        init_socket_handlers(socketio, db)
        db.create_all()
    
    return app

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)