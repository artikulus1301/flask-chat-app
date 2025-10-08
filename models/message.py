from app import db
from datetime import datetime

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), default='text')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'text': self.text,
            'timestamp': self.timestamp.strftime('%H:%M:%S'),
            'type': self.message_type
        }