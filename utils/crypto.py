import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib

class CryptoManager:
    """Менеджер шифрования для E2E сообщений"""
    
    def __init__(self):
        self.fernet = None
        
    def generate_key_from_password(self, password, salt=None):
        """Генерация ключа из пароля с использованием PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def initialize_fernet(self, key):
        """Инициализация Fernet с заданным ключом"""
        self.fernet = Fernet(key)
    
    def encrypt_message(self, message):
        """Шифрование сообщения"""
        if not self.fernet:
            raise ValueError("Fernet not initialized. Call initialize_fernet first.")
        
        if not message:
            return message
            
        encrypted = self.fernet.encrypt(message.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_message(self, encrypted_message):
        """Дешифрование сообщения"""
        if not self.fernet:
            raise ValueError("Fernet not initialized. Call initialize_fernet first.")
        
        if not encrypted_message:
            return encrypted_message
            
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

# Глобальный экземпляр для серверного шифрования
crypto_manager = CryptoManager()

def generate_key():
    """Генерация случайного ключа Fernet"""
    return Fernet.generate_key().decode()

def encrypt_message(message, key=None):
    """Простое шифрование сообщения"""
    if not key:
        key = generate_key()
    
    fernet = Fernet(key.encode())
    encrypted = fernet.encrypt(message.encode())
    return base64.urlsafe_b64encode(encrypted).decode(), key

def decrypt_message(encrypted_message, key):
    """Простое дешифрование сообщения"""
    try:
        fernet = Fernet(key.encode())
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def hash_codeword(codeword):
    """Хеширование кодового слова для безопасного хранения"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        codeword.encode('utf-8'),
        salt,
        100000
    )
    return base64.b64encode(salt + key).decode('utf-8')

def verify_codeword(codeword, hashed):
    """Проверка кодового слова против хеша"""
    try:
        decoded = base64.b64decode(hashed.encode('utf-8'))
        salt = decoded[:32]
        stored_key = decoded[32:]
        
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            codeword.encode('utf-8'),
            salt,
            100000
        )
        
        return new_key == stored_key
    except Exception:
        return False

def generate_shared_secret():
    """Генерация общего секрета для E2E шифрования между клиентами"""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

# Функции для работы с ключами на стороне клиента (будут использоваться в JS)
def generate_client_key_pair():
    """Генерация пары ключей для клиентского E2E шифрования"""
    # В реальной реализации здесь будет генерация RSA или ECDH ключей
    # Для демонстрации используем симметричное шифрование
    return {
        'public_key': generate_key(),
        'private_key': generate_key()
    }