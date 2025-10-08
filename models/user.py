from extensions import db
import uuid
from datetime import datetime

class User(db.Model):
    """Модель пользователя с UUID авторизацией"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    codeword = db.Column(db.String(100), nullable=False)  # Кодовое слово для "авторизации"
    username = db.Column(db.String(50), nullable=True)    # Отображаемое имя
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    
    messages = db.relationship('Message', backref='author', lazy=True, cascade='all, delete-orphan')
    groups = db.relationship('Group', secondary='user_groups', backref=db.backref('members', lazy=True))
    
    def to_dict(self):
        """Сериализация пользователя для JSON"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
    
    def __repr__(self):
        return f'<User {self.username} ({self.uuid})>'