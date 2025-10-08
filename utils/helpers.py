from datetime import datetime
import json

def format_timestamp(timestamp=None):
    """Форматирование времени"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.strftime('%H:%M:%S')

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class ChatLogger:
    """Логгер для чата"""
    
    @staticmethod
    def log_message(username, message, room='general'):
        """Логирование сообщения"""
        timestamp = format_timestamp()
        print(f'[{timestamp}] {room} | {username}: {message}')
    
    @staticmethod
    def log_event(event, details):
        """Логирование событий"""
        timestamp = format_timestamp()
        print(f'[{timestamp}] EVENT: {event} | {details}')
    
    @staticmethod
    def log_error(error, context=None):
        """Логирование ошибок"""
        timestamp = format_timestamp()
        if context:
            print(f'[{timestamp}] ERROR: {error} | Context: {context}')
        else:
            print(f'[{timestamp}] ERROR: {error}')