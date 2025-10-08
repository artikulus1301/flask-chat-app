from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit

bp = Blueprint('chat', __name__)

online_users = {}

def init_socket_handlers(socketio, db):
    from models.message import Message
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Client connected: {request.sid}')
        emit('connected', {'message': 'Connected to chat server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Client disconnected: {request.sid}')
        for sid, username in list(online_users.items()):
            if sid == request.sid:
                del online_users[sid]
                emit('system_message', {
                    'msg': f'🔴 {username} покинул чат',
                    'type': 'user_leave'
                }, broadcast=True)
                emit('user_count', {'count': len(online_users)}, broadcast=True)
                break

    @socketio.on('user_join')
    def handle_user_join(data):
        try:
            username = data.get('username', '').strip()
            
            if not username or len(username) < 2 or len(username) > 20:
                emit('join_error', {'error': 'Invalid username'})
                return
            
            if username in online_users.values():
                emit('join_error', {'error': 'Username already taken'})
                return
            
            online_users[request.sid] = username
            
            system_msg = Message(
                username='System',
                text=f'{username} присоединился к чату',
                message_type='user_join'
            )
            db.session.add(system_msg)
            db.session.commit()
            
            emit('join_success', {'username': username})
            emit('system_message', {
                'msg': f'🟢 {username} присоединился к чату',
                'type': 'user_join'
            }, broadcast=True)
            emit('user_count', {'count': len(online_users)}, broadcast=True)
            
        except Exception as e:
            emit('join_error', {'error': 'Internal server error'})

    @socketio.on('message')
    def handle_message(data):
        try:
            text = data.get('text', '').strip()
            username = online_users.get(request.sid)
            
            if not username:
                emit('message_error', {'error': 'You must join chat first'})
                return
            
            if not text:
                emit('message_error', {'error': 'Message cannot be empty'})
                return
            
            message = Message(
                username=username,
                text=text,
                message_type='text'
            )
            db.session.add(message)
            db.session.commit()
            
            emit('new_message', {
                'id': message.id,
                'username': username,
                'text': text,
                'timestamp': message.timestamp.strftime('%H:%M:%S'),
                'type': 'text'
            }, broadcast=True)
            
        except Exception as e:
            emit('message_error', {'error': 'Failed to send message'})

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/messages')
def get_messages():
    from models.message import Message
    try:
        messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in reversed(messages)]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500