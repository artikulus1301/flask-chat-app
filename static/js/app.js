// Main Application JavaScript
class ChatApp {
    constructor() {
        this.socket = null;
        this.currentUser = null;
        this.currentGroup = null;
        this.isEncrypted = false;
        this.typingTimer = null;
        
        this.initializeApp();
    }

    initializeApp() {
        this.setupEventListeners();
        this.connectSocket();
        this.loadUserData();
    }

    connectSocket() {
        this.socket = io({
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });

        this.setupSocketHandlers();
    }

    setupSocketHandlers() {
        // Basic connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.joinChat();
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.showDisconnectMessage();
        });

        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.showError('Ошибка подключения к серверу');
        });

        // Chat events
        this.socket.on('new_message', (data) => {
            this.handleNewMessage(data);
        });

        this.socket.on('message_history', (data) => {
            this.displayMessageHistory(data.messages);
        });

        this.socket.on('user_status', (data) => {
            this.updateUserStatus(data);
        });

        this.socket.on('user_typing', (data) => {
            this.showTypingIndicator(data);
        });

        this.socket.on('user_count', (data) => {
            this.updateOnlineCount(data.count);
        });

        this.socket.on('system_message', (data) => {
            this.displaySystemMessage(data);
        });

        // Error events
        this.socket.on('error', (data) => {
            this.showError(data.message);
        });

        this.socket.on('message_error', (data) => {
            this.showError(data.error);
        });
    }

    setupEventListeners() {
        // Send message
        const sendBtn = document.getElementById('send-btn');
        const messageInput = document.getElementById('message-input');
        
        if (sendBtn && messageInput) {
            sendBtn.addEventListener('click', () => this.sendMessage());
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Typing indicators
            messageInput.addEventListener('input', () => {
                this.handleTypingStart();
            });

            messageInput.addEventListener('blur', () => {
                this.handleTypingStop();
            });
        }

        // File upload
        const fileInput = document.getElementById('file-input');
        const fileUploadBtn = document.getElementById('file-upload-btn');
        
        if (fileInput && fileUploadBtn) {
            fileUploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // Encryption toggle
        const encryptionToggle = document.getElementById('encryption-toggle');
        if (encryptionToggle) {
            encryptionToggle.addEventListener('click', () => this.toggleEncryption());
        }

        // Character counter
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('input', () => this.updateCharCount());
        }

        // Group creation
        const createGroupBtn = document.getElementById('create-group-btn');
        if (createGroupBtn) {
            createGroupBtn.addEventListener('click', () => this.showCreateGroupModal());
        }

        // Modal handlers
        this.setupModalHandlers();
    }

    async joinChat() {
        if (!this.currentUser?.uuid) {
            console.warn('No user UUID available');
            return;
        }

        try {
            this.socket.emit('user_join', {
                user_uuid: this.currentUser.uuid
            });
        } catch (error) {
            console.error('Error joining chat:', error);
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const content = messageInput?.value.trim();
        
        if (!content) return;

        try {
            let messageData = {
                content: content,
                message_type: 'text',
                group_id: this.currentGroup?.id || null
            };

            // Apply encryption if enabled
            if (this.isEncrypted && chatCrypto.isEnabled) {
                const encrypted = await chatCrypto.encryptMessage(content);
                messageData = {
                    ...messageData,
                    content: encrypted.content,
                    is_encrypted: encrypted.encrypted,
                    encryption_key: encrypted.key
                };
            }

            this.socket.emit('send_message', messageData);
            
            // Clear input
            if (messageInput) {
                messageInput.value = '';
                messageInput.style.height = 'auto';
                this.updateCharCount();
                this.handleTypingStop();
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Ошибка отправки сообщения');
        }
    }

    handleNewMessage(messageData) {
        // Decrypt message if needed
        this.decryptMessage(messageData).then(decryptedData => {
            this.displayMessage(decryptedData);
            this.scrollToBottom();
        });
    }

    async decryptMessage(messageData) {
        if (messageData.is_encrypted && messageData.encryption_key) {
            try {
                const decryptedContent = await chatCrypto.decryptMessage(
                    { encrypted: true, content: messageData.content },
                    messageData.encryption_key
                );
                return {
                    ...messageData,
                    content: decryptedContent,
                    decrypted: true
                };
            } catch (error) {
                console.error('Decryption error:', error);
                return {
                    ...messageData,
                    content: '🔒 [Не удалось расшифровать сообщение]',
                    decryption_failed: true
                };
            }
        }
        return messageData;
    }

    displayMessage(messageData) {
        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) return;

        // Remove empty state if it exists
        const emptyState = document.getElementById('empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        const messageElement = this.createMessageElement(messageData);
        messagesContainer.appendChild(messageElement);
    }

    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message fade-in ${this.isOwnMessage(messageData) ? 'own' : 'other'}`;

        const isSystem = messageData.message_type === 'system';
        if (isSystem) {
            messageDiv.className = 'message system';
        }

        const timestamp = new Date(messageData.created_at).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        let content = `
            <div class="message-header">
                <span class="message-username">${this.escapeHtml(messageData.user?.username || 'Unknown')}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(messageData.content)}</div>
        `;

        if (messageData.is_encrypted) {
            content += `<div class="encryption-badge">🔒 Зашифровано</div>`;
        }

        if (messageData.file_url) {
            content += this.createFileElement(messageData);
        }

        messageDiv.innerHTML = content;
        return messageDiv;
    }

    createFileElement(messageData) {
        const fileExt = messageData.file_name?.split('.').pop()?.toLowerCase() || 'file';
        const fileIcons = {
            'pdf': '📕',
            'doc': '📄', 'docx': '📄',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'mp4': '🎥', 'avi': '🎥', 'mov': '🎥',
            'mp3': '🎵', 'wav': '🎵',
            'zip': '📦', 'rar': '📦',
            'default': '📎'
        };

        const icon = fileIcons[fileExt] || fileIcons.default;

        return `
            <div class="message-file">
                <span class="file-icon">${icon}</span>
                <a href="${messageData.file_url}" target="_blank" class="file-link">
                    ${this.escapeHtml(messageData.file_name)}
                </a>
            </div>
        `;
    }

    displayMessageHistory(messages) {
        const messagesContainer = document.getElementById('messages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = '';

        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="empty-state" id="empty-state">
                    <p>Нет сообщений. Будьте первым!</p>
                </div>
            `;
            return;
        }

        messages.forEach(message => {
            this.displayMessage(message);
        });

        this.scrollToBottom();
    }

    displaySystemMessage(data) {
        const systemMessage = {
            content: data.msg,
            message_type: 'system',
            created_at: new Date().toISOString(),
            user: null
        };
        
        this.displayMessage(systemMessage);
    }

    updateUserStatus(data) {
        // Update online users list
        this.updateOnlineUsersList();
        
        // Show status notification
        if (data.action === 'connected') {
            this.showNotification(`${data.username} подключился`);
        } else if (data.action === 'disconnected') {
            this.showNotification(`${data.username} отключился`);
        }
    }

    updateOnlineUsersList() {
        // This would be implemented to fetch and display online users
        console.log('Updating online users list...');
    }

    updateOnlineCount(count) {
        const countElement = document.getElementById('online-count-text');
        const usersCountElement = document.getElementById('online-users-count');
        
        if (countElement) {
            countElement.textContent = `${count} онлайн`;
        }
        
        if (usersCountElement) {
            usersCountElement.textContent = count;
        }
    }

    showTypingIndicator(data) {
        const indicator = document.getElementById('typing-indicator');
        if (!indicator) return;

        if (data.is_typing) {
            indicator.textContent = `${data.username} печатает...`;
            indicator.classList.add('typing-indicator');
        } else {
            indicator.textContent = '';
            indicator.classList.remove('typing-indicator');
        }
    }

    handleTypingStart() {
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        } else {
            this.socket.emit('typing', {
                is_typing: true,
                group_id: this.currentGroup?.id
            });
        }

        this.typingTimer = setTimeout(() => {
            this.handleTypingStop();
        }, 1000);
    }

    handleTypingStop() {
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }

        this.socket.emit('typing', {
            is_typing: false,
            group_id: this.currentGroup?.id
        });
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_uuid', this.currentUser.uuid);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Send message with file
                this.socket.emit('send_message', {
                    content: 'Прикрепленный файл',
                    message_type: 'file',
                    file_url: result.file_url,
                    file_name: result.file_name,
                    group_id: this.currentGroup?.id
                });
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            console.error('File upload error:', error);
            this.showError('Ошибка загрузки файла');
        }

        // Reset file input
        event.target.value = '';
    }

    toggleEncryption() {
        this.isEncrypted = chatCrypto.toggleEncryption();
        
        const statusElement = document.getElementById('encryption-status');
        const toggleButton = document.getElementById('encryption-toggle');
        
        if (statusElement && toggleButton) {
            if (this.isEncrypted) {
                statusElement.textContent = 'Шифрование включено';
                statusElement.className = 'encryption-on';
                toggleButton.textContent = '🔐';
                toggleButton.title = 'Выключить шифрование';
            } else {
                statusElement.textContent = 'Шифрование выключено';
                statusElement.className = 'encryption-off';
                toggleButton.textContent = '🔓';
                toggleButton.title = 'Включить шифрование';
            }
        }
    }

    updateCharCount() {
        const messageInput = document.getElementById('message-input');
        const charCount = document.getElementById('char-count');
        
        if (messageInput && charCount) {
            const count = messageInput.value.length;
            charCount.textContent = `${count}/2000`;
            
            // Update send button state
            const sendBtn = document.getElementById('send-btn');
            if (sendBtn) {
                sendBtn.disabled = count === 0;
            }
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    showError(message) {
        // Implement error notification system
        console.error('Error:', message);
        alert(`Ошибка: ${message}`);
    }

    showNotification(message) {
        // Implement notification system
        console.log('Notification:', message);
    }

    showDisconnectMessage() {
        this.showError('Соединение с сервером потеряно. Попытка переподключения...');
    }

    isOwnMessage(messageData) {
        return messageData.user?.uuid === this.currentUser?.uuid;
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    loadUserData() {
        // Load user data from session or localStorage
        try {
            const userData = localStorage.getItem('chat_user');
            if (userData) {
                this.currentUser = JSON.parse(userData);
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    setupModalHandlers() {
        // Modal close handlers
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const closeBtn = modal.querySelector('.close-modal');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    modal.classList.remove('show');
                });
            }

            // Close on outside click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
        });
    }

    showCreateGroupModal() {
        const modal = document.getElementById('create-group-modal');
        if (modal) {
            modal.classList.add('show');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatApp = new ChatApp();
});

// Global functions for template usage
function initializeChat() {
    // Already handled by ChatApp constructor
}

function initializeGroupChat() {
    // Group-specific initialization
    if (window.chatApp) {
        window.chatApp.currentGroup = window.GROUP_DATA;
    }
}