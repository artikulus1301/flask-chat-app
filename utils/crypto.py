import base64
import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoManager:
    """Менеджер шифрования для E2E сообщений (серверная часть)."""

    def __init__(self):
        self.fernet = None

    def generate_key_from_password(self, password: str, salt: bytes = None):
        """Генерация ключа из пароля с использованием PBKDF2 (SHA256)."""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def initialize_fernet(self, key: bytes):
        """Инициализация шифра Fernet с заданным ключом."""
        self.fernet = Fernet(key)

    def encrypt_message(self, message: str) -> str:
        """Шифрование сообщения (base64)."""
        if not self.fernet:
            raise ValueError("Fernet not initialized. Call initialize_fernet first.")

        if not message:
            return ""

        encrypted = self.fernet.encrypt(message.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_message(self, encrypted_message: str) -> str:
        """Дешифрование сообщения (base64)."""
        if not self.fernet:
            raise ValueError("Fernet not initialized. Call initialize_fernet first.")

        if not encrypted_message:
            return ""

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


# Глобальный экземпляр для использования в приложении
crypto_manager = CryptoManager()


# ================================================================
# Простые функции для вспомогательных задач
# ================================================================

def generate_key() -> str:
    """Генерация случайного ключа Fernet (в base64)."""
    return Fernet.generate_key().decode()


def encrypt_message(message: str, key: str = None) -> tuple[str, str]:
    """Шифрование сообщения с заданным ключом (или новым)."""
    if not key:
        key = generate_key()

    fernet = Fernet(key.encode())
    encrypted = fernet.encrypt(message.encode())
    return base64.urlsafe_b64encode(encrypted).decode(), key


def decrypt_message(encrypted_message: str, key: str) -> str:
    """Дешифрование сообщения."""
    try:
        fernet = Fernet(key.encode())
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def hash_codeword(codeword: str) -> str:
    """Хеширование кодового слова (для хранения в БД)."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        codeword.encode('utf-8'),
        salt,
        100_000
    )
    return base64.b64encode(salt + key).decode('utf-8')


def verify_codeword(codeword: str, hashed: str) -> bool:
    """Проверка кодового слова против хеша."""
    try:
        decoded = base64.b64decode(hashed.encode('utf-8'))
        salt, stored_key = decoded[:32], decoded[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            codeword.encode('utf-8'),
            salt,
            100_000
        )
        return new_key == stored_key
    except Exception:
        return False


def generate_shared_secret() -> str:
    """Генерация общего секрета для E2E-шифрования между клиентами."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def generate_client_key_pair() -> dict:
    """
    Генерация пары ключей для клиентского E2E шифрования.
    В реальном приложении тут нужно использовать RSA или ECDH.
    """
    return {
        'public_key': generate_key(),
        'private_key': generate_key()
    }
