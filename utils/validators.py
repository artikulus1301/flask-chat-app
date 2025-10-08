import re
import os
from flask import current_app
from urllib.parse import urlparse

def validate_message(content, message_type='text', file_url=None):
    """
    Валидация сообщения
    Возвращает (is_valid, error_message)
    """
    # Проверка на пустое сообщение без файла
    if not content and not file_url and message_type == 'text':
        return False, "Сообщение не может быть пустым"
    
    # Проверка длины текстового сообщения
    if content and len(content) > current_app.config.get('MESSAGE_MAX_LENGTH', 2000):
        return False, f"Сообщение слишком длинное (максимум {current_app.config.get('MESSAGE_MAX_LENGTH', 2000)} символов)"
    
    # Проверка на запрещенный контент
    forbidden_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+=',
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, content or '', re.IGNORECASE):
            return False, "Сообщение содержит запрещенный контент"
    
    # Проверка типа сообщения
    allowed_types = ['text', 'image', 'file', 'system']
    if message_type not in allowed_types:
        return False, f"Недопустимый тип сообщения: {message_type}"
    
    return True, "OK"

def validate_file_upload(filename, file_size):
    """
    Валидация загружаемого файла
    Возвращает (is_valid, error_message)
    """
    if not filename:
        return False, "Файл не выбран"
    
    # Проверка расширения файла
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    if '.' not in filename:
        return False, "Файл должен иметь расширение"
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Тип файла {ext} не поддерживается"
    
    # Проверка размера файла
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 25 * 1024 * 1024)
    if file_size > max_size:
        return False, f"Файл слишком большой (максимум {max_size // (1024*1024)} МБ)"
    
    # Проверка имени файла
    if len(filename) > 255:
        return False, "Имя файла слишком длинное"
    
    # Проверка на опасные имена файлов
    dangerous_patterns = [r'\.\./', r'\.\.\\', r'/', r'\\']
    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            return False, "Недопустимое имя файла"
    
    return True, "OK"

def validate_group_data(name, description, is_private):
    """
    Валидация данных группы
    Возвращает (is_valid, error_message)
    """
    # Проверка названия группы
    if not name or len(name.strip()) == 0:
        return False, "Название группы не может быть пустым"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Название группы должно содержать минимум 2 символа"
    
    if len(name) > 100:
        return False, "Название группы не может превышать 100 символов"
    
    # Проверка описания группы
    if description and len(description) > 500:
        return False, "Описание группы не может превышать 500 символов"
    
    # Проверка типа приватности
    if not isinstance(is_private, bool):
        return False, "Неверный формат приватности группы"
    
    # Проверка на запрещенные слова в названии
    forbidden_words = ['admin', 'system', 'root', 'official', 'support']
    if any(word in name.lower() for word in forbidden_words):
        return False, "Это название группы запрещено"
    
    return True, "OK"

def validate_url(url):
    """Валидация URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def validate_email(email):
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """
    Проверка сложности пароля
    Возвращает (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    
    if len(password) > 128:
        return False, "Пароль не может превышать 128 символов"
    
    # Проверка на наличие цифр
    if not re.search(r'\d', password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    
    # Проверка на наличие букв в разных регистрах
    if not re.search(r'[a-z]', password) or not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать буквы в верхнем и нижнем регистре"
    
    # Проверка на специальные символы
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Пароль должен содержать хотя бы один специальный символ"
    
    return True, "Пароль надежный"

def validate_user_uuid(uuid_string):
    """Валидация UUID пользователя"""
    from utils.helpers import is_valid_uuid
    return is_valid_uuid(uuid_string)

def sanitize_filename(filename):
    """Очистка имени файла от потенциально опасных символов"""
    if not filename:
        return "file"
    
    # Удаление опасных символов
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Ограничение длины
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    return filename