from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# Instantiate extensions here to avoid circular imports between app and models
db = SQLAlchemy()
socketio = SocketIO()
