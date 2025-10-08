// End-to-End Encryption for Client-Side
class ChatEncryption {
    constructor() {
        this.isEnabled = false;
        this.currentKey = null;
        this.algorithm = 'AES-GCM';
    }

    // Генерация ключа шифрования
    async generateKey() {
        try {
            const key = await crypto.subtle.generateKey(
                {
                    name: this.algorithm,
                    length: 256,
                },
                true,
                ['encrypt', 'decrypt']
            );
            
            // Экспорт ключа для хранения
            const exported = await crypto.subtle.exportKey('jwk', key);
            this.currentKey = exported;
            
            return exported;
        } catch (error) {
            console.error('Error generating key:', error);
            throw error;
        }
    }

    // Импорт ключа из JSON
    async importKey(keyData) {
        try {
            const key = await crypto.subtle.importKey(
                'jwk',
                keyData,
                {
                    name: this.algorithm,
                    length: 256,
                },
                true,
                ['encrypt', 'decrypt']
            );
            
            this.currentKey = keyData;
            return key;
        } catch (error) {
            console.error('Error importing key:', error);
            throw error;
        }
    }

    // Шифрование сообщения
    async encryptMessage(message) {
        if (!this.isEnabled || !this.currentKey) {
            return {
                encrypted: false,
                content: message
            };
        }

        try {
            const key = await this.importKey(this.currentKey);
            const encoder = new TextEncoder();
            const data = encoder.encode(message);
            
            // Генерация IV (Initialization Vector)
            const iv = crypto.getRandomValues(new Uint8Array(12));
            
            // Шифрование
            const encrypted = await crypto.subtle.encrypt(
                {
                    name: this.algorithm,
                    iv: iv
                },
                key,
                data
            );
            
            // Объединение IV и зашифрованных данных
            const combined = new Uint8Array(iv.length + encrypted.byteLength);
            combined.set(iv);
            combined.set(new Uint8Array(encrypted), iv.length);
            
            // Конвертация в base64 для передачи
            const encryptedBase64 = btoa(String.fromCharCode(...combined));
            
            return {
                encrypted: true,
                content: encryptedBase64,
                key: JSON.stringify(this.currentKey)
            };
            
        } catch (error) {
            console.error('Encryption error:', error);
            throw error;
        }
    }

    // Дешифрование сообщения
    async decryptMessage(encryptedData, keyData) {
        if (!encryptedData.encrypted) {
            return encryptedData.content;
        }

        try {
            const key = await this.importKey(JSON.parse(keyData || this.currentKey));
            
            // Декодирование из base64
            const encryptedBytes = Uint8Array.from(atob(encryptedData.content), c => c.charCodeAt(0));
            
            // Извлечение IV и зашифрованных данных
            const iv = encryptedBytes.slice(0, 12);
            const data = encryptedBytes.slice(12);
            
            // Дешифрование
            const decrypted = await crypto.subtle.decrypt(
                {
                    name: this.algorithm,
                    iv: iv
                },
                key,
                data
            );
            
            const decoder = new TextDecoder();
            return decoder.decode(decrypted);
            
        } catch (error) {
            console.error('Decryption error:', error);
            return '🔒 [Не удалось расшифровать сообщение]';
        }
    }

    // Включение/выключение шифрования
    toggleEncryption() {
        this.isEnabled = !this.isEnabled;
        
        if (this.isEnabled && !this.currentKey) {
            this.generateKey().then(key => {
                console.log('Encryption enabled with key:', key.k);
                this.showKeyWarning();
            });
        }
        
        return this.isEnabled;
    }

    // Предупреждение о важности ключа
    showKeyWarning() {
        if (!this.currentKey) return;
        
        const warning = `
            🔐 Шифрование включено!
            
            Ваш ключ шифрования:
            ${this.currentKey.k}
            
            ⚠️ Сохраните этот ключ в безопасном месте!
            Без него вы не сможете прочитать свои зашифрованные сообщения.
        `;
        
        if (confirm(warning)) {
            // Пользователь подтвердил, что сохранил ключ
            console.log('User acknowledged encryption key');
        }
    }

    // Экспорт ключа для резервного копирования
    exportKey() {
        if (!this.currentKey) {
            return null;
        }
        
        return {
            key: this.currentKey,
            algorithm: this.algorithm,
            timestamp: new Date().toISOString()
        };
    }

    // Импорт ключа из резервной копии
    async importBackup(backupData) {
        try {
            if (backupData.algorithm !== this.algorithm) {
                throw new Error('Unsupported encryption algorithm');
            }
            
            await this.importKey(backupData.key);
            this.isEnabled = true;
            return true;
        } catch (error) {
            console.error('Backup import error:', error);
            throw error;
        }
    }
}

// Глобальный экземпляр шифрования
const chatCrypto = new ChatEncryption();

// Утилиты для работы с ключами
class KeyManager {
    static generateSharedSecret() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode(...array));
    }

    static deriveKeyFromPassword(password, salt) {
        const encoder = new TextEncoder();
        return crypto.subtle.importKey(
            'raw',
            encoder.encode(password),
            'PBKDF2',
            false,
            ['deriveKey']
        ).then(baseKey => {
            return crypto.subtle.deriveKey(
                {
                    name: 'PBKDF2',
                    salt: encoder.encode(salt),
                    iterations: 100000,
                    hash: 'SHA-256'
                },
                baseKey,
                {
                    name: 'AES-GCM',
                    length: 256
                },
                true,
                ['encrypt', 'decrypt']
            );
        });
    }

    static async encryptWithPassword(message, password) {
        const salt = crypto.getRandomValues(new Uint8Array(16));
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const key = await this.deriveKeyFromPassword(password, salt);
        
        const encoder = new TextEncoder();
        const data = encoder.encode(message);
        
        const encrypted = await crypto.subtle.encrypt(
            {
                name: 'AES-GCM',
                iv: iv
            },
            key,
            data
        );
        
        const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength);
        combined.set(salt);
        combined.set(iv, salt.length);
        combined.set(new Uint8Array(encrypted), salt.length + iv.length);
        
        return btoa(String.fromCharCode(...combined));
    }

    static async decryptWithPassword(encryptedData, password) {
        try {
            const encryptedBytes = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
            
            const salt = encryptedBytes.slice(0, 16);
            const iv = encryptedBytes.slice(16, 28);
            const data = encryptedBytes.slice(28);
            
            const key = await this.deriveKeyFromPassword(password, salt);
            
            const decrypted = await crypto.subtle.decrypt(
                {
                    name: 'AES-GCM',
                    iv: iv
                },
                key,
                data
            );
            
            const decoder = new TextDecoder();
            return decoder.decode(decrypted);
        } catch (error) {
            throw new Error('Decryption failed - wrong password or corrupted data');
        }
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatEncryption, KeyManager };
}