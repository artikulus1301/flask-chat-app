import html
import re

def sanitize_input(text, max_length=500):
    """Очистка и валидация ввода"""
    if text is None:
        return None
    
    text = str(text).strip()
    
    if not text or len(text) > max_length:
        return None
    
    safe_text = html.escape(text)
    
    safe_text = re.sub(r'\s+', ' ', safe_text)
    
    return safe_text

def is_valid_username(username):
    """Проверка имени пользователя"""
    if not username or len(username) > 20 or len(username) < 2:
        return False

    pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9\s\_\-\.]+$'
    return bool(re.match(pattern, username))

def is_valid_message(text):
    """Проверка сообщения"""
    if not text or len(text) > 500:
        return False

    if text.strip() == '':
        return False
    
    return True