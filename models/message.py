from extensions import db
import uuid
from datetime import datetime

class Message(db.Model):
    """Модель сообщения с поддержкой E2E шифрования"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)  # Текст сообщения (может быть зашифрован)
    is_encrypted = db.Column(db.Boolean, default=False)
    encryption_key = db.Column(db.String(500), nullable=True)  # Ключ для E2E (если используется)
    
    # Тип сообщения: 'text', 'image', 'file', 'system'
    message_type = db.Column(db.String(20), default='text')
    file_url = db.Column(db.String(500), nullable=True)  # URL для загруженных файлов
    file_name = db.Column(db.String(255), nullable=True)  # Оригинальное имя файла
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)  # None = общий чат
    
    def to_dict(self):
        """Сериализация сообщения для JSON"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'content': self.content,
            'is_encrypted': self.is_encrypted,
            'message_type': self.message_type,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'created_at': self.created_at.isoformat(),
            'user': self.author.to_dict() if self.author else None,
            'group_id': self.group_id
        }
    
    def __repr__(self):
        return f'<Message {self.uuid} from User {self.user_id}>'

# Дополнительные модели для групп (создадим позже, но оставим ForeignKey)
class Group(db.Model):
    """Модель группы/комнаты чата"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    
    messages = db.relationship('Message', backref='group', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'is_private': self.is_private,
            'member_count': len(self.members)
        }

user_groups = db.Table('user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)