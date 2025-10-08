from extensions import db
import uuid
from datetime import datetime
import hashlib


class User(db.Model):
    """Модель пользователя с UUID и кодовым словом для авторизации"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Храним хеш кодового слова для безопасности
    codeword_hash = db.Column(db.String(64), nullable=False)  # SHA256 hash
    username = db.Column(db.String(50), nullable=False, unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)

    # Отношения
    messages = db.relationship(
        'Message',
        backref='author',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    groups = db.relationship(
        'Group',
        secondary='user_groups',
        back_populates='members',
        lazy='dynamic'
    )

    def to_dict(self, include_groups=False):
        """Сериализация пользователя для JSON-ответа"""
        data = {
            'uuid': self.uuid,
            'username': self.username,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }
        if include_groups:
            data['groups'] = [group.to_dict() for group in self.groups]
        return data

    def set_codeword(self, codeword):
        """Установить хеш кодового слова"""
        self.codeword_hash = hashlib.sha256(codeword.encode()).hexdigest()

    def check_codeword(self, codeword):
        """Проверить кодовое слово"""
        return self.codeword_hash == hashlib.sha256(codeword.encode()).hexdigest()

    def touch(self):
        """Обновить активность пользователя"""
        self.last_seen = datetime.utcnow()
        self.is_online = True
        db.session.add(self)

    def logout(self):
        """Обновить статус при выходе"""
        self.is_online = False
        db.session.add(self)

    def __repr__(self):
        return f"<User {self.username}>"