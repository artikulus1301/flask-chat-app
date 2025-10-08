class Chat {
    constructor() {
        this.socket = io();
        this.currentUsername = '';
        this.isJoined = false;
        this.typingTimer = null;
        this.initializeEvents();
        this.loadMessageHistory();
    }
    
    initializeEvents() {
     
        this.socket.on('connect', this.handleConnect.bind(this));
        this.socket.on('disconnect', this.handleDisconnect.bind(this));
        this.socket.on('new_message', this.handleNewMessage.bind(this));
        this.socket.on('system_message', this.handleSystemMessage.bind(this));
        this.socket.on('user_count', this.handleUserCount.bind(this));
        this.socket.on('user_typing', this.handleUserTyping.bind(this));
        this.socket.on('join_success', this.handleJoinSuccess.bind(this));
        this.socket.on('join_error', this.handleJoinError.bind(this));
        this.socket.on('message_error', this.handleMessageError.bind(this));
        
    
        document.getElementById('joinBtn').addEventListener('click', 
            this.joinChat.bind(this));
        document.getElementById('sendBtn').addEventListener('click', 
            this.sendMessage.bind(this));
        
        const msgInput = document.getElementById('msg');
        const usernameInput = document.getElementById('username');
        
        msgInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        msgInput.addEventListener('input', this.handleTyping.bind(this));
        
        usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinChat();
        });
        
        window.addEventListener('beforeunload', this.leaveChat.bind(this));
    }
    
    handleConnect() {
        this.showStatus('✅ Подключено к серверу', 'success');
    }
    
    handleDisconnect() {
        this.showStatus('❌ Отключено от сервера', 'error');
    }
    
    handleJoinSuccess(data) {
        this.currentUsername = data.username;
        this.isJoined = true;
        
        document.getElementById('username').disabled = true;
        document.getElementById('joinBtn').disabled = true;
        document.getElementById('msg').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        
        this.showStatus(`✅ Добро пожаловать, ${data.username}!`, 'success');
        document.getElementById('msg').focus();
    }
    
    handleJoinError(data) {
        this.showStatus(`❌ Ошибка: ${data.error}`, 'error');
    }
    
    handleNewMessage(data) {
        this.addMessage(data.text, data.username, 'user-message', data.timestamp);
    }
    
    handleSystemMessage(data) {
        const typeClass = data.type === 'user_join' ? 'join-message' : 
                         data.type === 'user_leave' ? 'leave-message' : 'system-message';
        this.addMessage(data.msg, 'System', typeClass, new Date().toLocaleTimeString());
    }
    
    handleUserCount(data) {
        document.getElementById('onlineCount').textContent = data.count;
    }
    
    handleUserTyping(data) {
        this.showTypingIndicator(data.username, data.is_typing);
    }
    
    handleMessageError(data) {
        this.showStatus(`❌ ${data.error}`, 'error');
    }
    
    handleTyping() {
        if (!this.isJoined) return;
       
        this.socket.emit('typing', { is_typing: true });
       
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(() => {
            this.socket.emit('typing', { is_typing: false });
        }, 1000);
    }
    
    joinChat() {
        const username = document.getElementById('username').value.trim();
        
        if (!username) {
            this.showStatus('❌ Введите имя пользователя', 'error');
            return;
        }
        
        if (username.length < 2 || username.length > 20) {
            this.showStatus('❌ Имя должно быть от 2 до 20 символов', 'error');
            return;
        }
        
        this.socket.emit('user_join', { username: username });
    }
    
    sendMessage() {
        if (!this.isJoined) {
            this.showStatus('❌ Сначала войдите в чат', 'error');
            return;
        }
        
        const msgInput = document.getElementById('msg');
        const message = msgInput.value.trim();
        
        if (!message) {
            this.showStatus('❌ Введите сообщение', 'error');
            return;
        }
        
        if (message.length > 500) {
            this.showStatus('❌ Сообщение слишком длинное', 'error');
            return;
        }
        
        this.socket.emit('message', { text: message });
        msgInput.value = '';
        
        this.socket.emit('typing', { is_typing: false });
    }
    
    leaveChat() {
        if (this.isJoined) {
        }
    }
    
    addMessage(text, username, className, timestamp = null) {
        const chat = document.getElementById('chat');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        
        if (!timestamp) {
            timestamp = new Date().toLocaleTimeString();
        }
        
        if (className === 'user-message') {
            messageDiv.innerHTML = `
                <div class="message-username">${this.escapeHtml(username)}</div>
                <div class="message-text">${this.escapeHtml(text)}</div>
                <div class="message-time">${timestamp}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-text">${this.escapeHtml(text)}</div>
            `;
        }
        
        chat.appendChild(messageDiv);
        chat.scrollTop = chat.scrollHeight;
    }
    
    showStatus(message, type) {
        const chat = document.getElementById('chat');
        const statusDiv = document.createElement('div');
        statusDiv.className = `status-message status-${type}`;
        statusDiv.textContent = message;
        
        chat.appendChild(statusDiv);
        chat.scrollTop = chat.scrollHeight;
        
        setTimeout(() => {
            if (statusDiv.parentNode) {
                statusDiv.remove();
            }
        }, 5000);
    }
    
    showTypingIndicator(username, isTyping) {
        let indicator = document.getElementById('typing-indicator');
        
        if (isTyping) {
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'typing-indicator';
                indicator.className = 'typing-indicator';
                document.getElementById('chat').appendChild(indicator);
            }
            indicator.textContent = `${username} печатает...`;
        } else {
            if (indicator) {
                indicator.remove();
            }
        }
    }
    
    async loadMessageHistory() {
        try {
            const response = await fetch('/api/messages?limit=50');
            const data = await response.json();
            
            if (data.success) {
                data.messages.forEach(msg => {
                    const className = msg.type === 'text' ? 'user-message' : 
                                   msg.type === 'user_join' ? 'join-message' : 'system-message';
                    this.addMessage(msg.text, msg.username, className, msg.timestamp);
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки истории:', error);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.chat = new Chat();
});