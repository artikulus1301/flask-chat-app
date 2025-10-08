from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from cryptography.fernet import Fernet
import os

# --- База данных ---
db = SQLAlchemy()

# --- Настройка SocketIO ---
# Инициализация без параметров — конфиг задаётся в app.py
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",  # работает и локально, и на Render
    ping_timeout=60,
    ping_interval=25,
)

# --- E2E Encryption (end-to-end) ---
class EncryptionManager:
    """Менеджер шифрования для сообщений и файлов."""

    def __init__(self, key_path="instance/e2e_key.key"):
        self.key_path = key_path
        os.makedirs(os.path.dirname(self.key_path), exist_ok=True)

        if not os.path.exists(self.key_path):
            # Создаём новый ключ, если файла нет
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
        else:
            with open(self.key_path, "rb") as f:
                key = f.read()

        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Шифрует строку и возвращает base64-текст."""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Расшифровывает строку, если возможно."""
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except Exception:
            return "[Ошибка расшифровки]"


# Инициализируем менеджер при запуске приложения
encryption = EncryptionManager()
