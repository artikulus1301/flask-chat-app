import uuid
import re
from datetime import datetime, timedelta
from flask import request
import html

def generate_uuid():
    """Генерация UUID строки"""
    return str(uuid.uuid4())

def generate_user_code(length=8):
    """Генерация читаемого кода для пользователя"""
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def validate_username(username):
    """
    Валидация имени пользователя
    Возвращает (is_valid, error_message)
    """
    if not username or len(username.strip()) == 0:
        return False, "Имя пользователя не может быть пустым"
    
    username = username.strip()
    
    if len(username) < 2:
        return False, "Имя пользователя должно содержать минимум 2 символа"
    
    if len(username) > 20:
        return False, "Имя пользователя не может превышать 20 символов"
    
    # Проверка на разрешенные символы
    if not re.match(r'^[a-zA-Z0-9а-яА-ЯёЁ_\-\. ]+$', username):
        return False, "Имя пользователя содержит недопустимые символы"
    
    # Запрещенные слова
    forbidden_words = ['admin', 'system', 'root', 'moderator', 'support']
    if any(word in username.lower() for word in forbidden_words):
        return False, "Это имя пользователя запрещено"
    
    return True, username

def sanitize_input(text):
    """Очистка входных данных от потенциально опасного контента"""
    if not text:
        return ""
    
    # Экранирование HTML
    text = html.escape(text)
    
    # Удаление потенциально опасных конструкций
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+=', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def format_timestamp(dt):
    """Форматирование времени для отображения"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "только что"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} мин назад"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} ч назад"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} дн назад"
    else:
        return dt.strftime("%d.%m.%Y %H:%M")

def get_client_ip():
    """Получение IP адреса клиента"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def truncate_text(text, max_length=100):
    """Обрезка текста с добавлением многоточия"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_valid_uuid(uuid_string):
    """Проверка валидности UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def generate_invite_code():
    """Генерация кода приглашения в группу"""
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))