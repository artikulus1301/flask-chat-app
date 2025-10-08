from extensions import db
import uuid
from datetime import datetime


# Ассоциативная таблица для связи пользователей и групп
user_groups = db.Table(
    'user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)


class Message(db.Model):
    """Модель сообщения с поддержкой E2E и файлов"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    content = db.Column(db.Text, nullable=False)  # Текст (возможно зашифрован)
    is_encrypted = db.Column(db.Boolean, default=False)
    encryption_key = db.Column(db.String(500), nullable=True)  # Хранится только при необходимости

    message_type = db.Column(db.String(20), default='text')  # text / image / file / system
    file_url = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Внешние ключи
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=True)

    def to_dict(self):
        """Подготовка к JSON-ответу"""
        return {
            'uuid': self.uuid,
            'content': self.content,
            'is_encrypted': self.is_encrypted,
            'message_type': self.message_type,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'created_at': self.created_at.isoformat(),
            'user': self.author.to_dict() if hasattr(self, 'author') and self.author else None,
            'group_id': self.group_id
        }

    def __repr__(self):
        return f"<Message {self.uuid} (user={self.user_id})>"


class Group(db.Model):
    """Модель группового или приватного чата"""
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    is_private = db.Column(db.Boolean, default=False)

    messages = db.relationship(
        'Message',
        backref='group',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    members = db.relationship(
        'User',
        secondary=user_groups,
        back_populates='groups',
        lazy='dynamic'
    )

    def to_dict(self):
        return {
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'is_private': self.is_private,
            'member_count': self.members.count() if hasattr(self.members, 'count') else len(self.members)
        }

    def __repr__(self):
        return f"<Group {self.name} ({self.uuid})>"
