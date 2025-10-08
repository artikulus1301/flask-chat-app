import uuid
import re
import html
import random
import string
from datetime import datetime, timedelta
from flask import request


def generate_uuid():
    """Генерация UUID строки"""
    return str(uuid.uuid4())


def generate_user_code(length=8):
    """Генерация читаемого кода для пользователя"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def validate_username(username):
    """
    Валидация имени пользователя
    Возвращает (is_valid, cleaned_username или error_message)
    """
    if not username or not username.strip():
        return False, "Имя пользователя не может быть пустым"

    username = username.strip()

    if len(username) < 2:
        return False, "Имя пользователя должно содержать минимум 2 символа"
    if len(username) > 20:
        return False, "Имя пользователя не может превышать 20 символов"

    if not re.match(r'^[a-zA-Z0-9а-яА-ЯёЁ_\-\. ]+$', username):
        return False, "Имя пользователя содержит недопустимые символы"

    forbidden_words = {'admin', 'system', 'root', 'moderator', 'support'}
    if any(word in username.lower() for word in forbidden_words):
        return False, "Это имя пользователя запрещено"

    return True, username


def sanitize_input(text):
    """Очистка входных данных от потенциально опасного контента"""
    if not text:
        return ""

    # Экранирование HTML и удаление вредных конструкций
    text = html.escape(text)
    text = re.sub(r'(?i)(javascript:|vbscript:|on\w+=)', '', text)

    # Убираем двойные пробелы и лишние переносы
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def format_timestamp(dt):
    """Форматирование времени для отображения в удобной форме"""
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
    """Получение IP адреса клиента, с учетом прокси"""
    ip_headers = ['X-Forwarded-For', 'X-Real-IP']
    for header in ip_headers:
        if header in request.headers:
            return request.headers[header].split(',')[0].strip()
    return request.remote_addr


def truncate_text(text, max_length=100):
    """Обрезка текста с добавлением многоточия"""
    if not text:
        return ""
    return text if len(text) <= max_length else text[:max_length - 3] + "..."


def is_valid_uuid(uuid_string):
    """Проверка валидности UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def generate_invite_code(length=6):
    """Генерация кода приглашения в группу"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
