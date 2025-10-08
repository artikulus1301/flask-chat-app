from flask import render_template, redirect, session
from flask import Blueprint, request, session, jsonify
from flask_socketio import emit, join_room, leave_room
from extensions import db
from models.user import User
from models.message import Message, Group
from datetime import datetime
import json

bp = Blueprint('chat', __name__)

# Временное хранилище для онлайн пользователей (в продакшене использовать Redis)
online_users = {}

def init_socket_handlers(socketio, db_instance):
    """Инициализация обработчиков SocketIO"""
    
    @socketio.on('connect')
    def handle_connect():
        """Обработчик подключения клиента"""
        print(f'Client connected: {request.sid}')
        
        # Проверяем авторизацию пользователя
        user_uuid = session.get('user_uuid')
        if user_uuid:
            user = User.query.filter_by(uuid=user_uuid).first()
            if user:
                # Обновляем статус пользователя
                user.is_online = True
                user.last_seen = datetime.utcnow()
                db_instance.session.commit()
                
                # Добавляем в онлайн список
                online_users[request.sid] = {
                    'user_id': user.id,
                    'username': user.username,
                    'uuid': user.uuid
                }
                
                emit('user_status', {
                    'user_id': user.id,
                    'username': user.username,
                    'is_online': True,
                    'action': 'connected'
                }, broadcast=True)
        
        emit('connected', {
            'message': 'Connected to chat server',
            'user_count': len(online_users)
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Обработчик отключения клиента"""
        print(f'Client disconnected: {request.sid}')
        
        user_info = online_users.get(request.sid)
        if user_info:
            # Обновляем статус пользователя в БД
            user = User.query.get(user_info['user_id'])
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                db_instance.session.commit()
                
                emit('user_status', {
                    'user_id': user.id,
                    'username': user.username,
                    'is_online': False,
                    'action': 'disconnected'
                }, broadcast=True)
            
            # Удаляем из онлайн списка
            del online_users[request.sid]
        
        emit('user_count', {'count': len(online_users)}, broadcast=True)

    @socketio.on('user_join')
    def handle_user_join(data):
        """Присоединение пользователя к чату (после авторизации)"""
        try:
            user_uuid = data.get('user_uuid')
            if not user_uuid:
                emit('join_error', {'error': 'User UUID required'})
                return
            
            user = User.query.filter_by(uuid=user_uuid).first()
            if not user:
                emit('join_error', {'error': 'User not found'})
                return
            
            # Сохраняем в сессии
            session['user_uuid'] = user.uuid
            session['user_id'] = user.id
            
            # Добавляем в онлайн список
            online_users[request.sid] = {
                'user_id': user.id,
                'username': user.username,
                'uuid': user.uuid
            }
            
            # Обновляем статус в БД
            user.is_online = True
            user.last_seen = datetime.utcnow()
            db_instance.session.commit()
            
            # Создаем системное сообщение о входе
            system_message = Message(
                content=f'{user.username} присоединился к чату',
                message_type='system',
                user_id=user.id
            )
            db_instance.session.add(system_message)
            db_instance.session.commit()
            
            emit('join_success', {
                'user': user.to_dict(),
                'message': 'Successfully joined chat'
            })
            
            emit('system_message', {
                'id': system_message.id,
                'content': f'🟢 {user.username} присоединился к чату',
                'type': 'user_join',
                'timestamp': system_message.created_at.isoformat(),
                'user': user.to_dict()
            }, broadcast=True)
            
            emit('user_count', {'count': len(online_users)}, broadcast=True)
            
        except Exception as e:
            emit('join_error', {'error': f'Internal server error: {str(e)}'})

    @socketio.on('join_room')
    def handle_join_room(data):
        """Присоединение к комнате/группе"""
        room_id = data.get('room_id')
        group_uuid = data.get('group_uuid')
        
        if not room_id and not group_uuid:
            emit('error', {'message': 'Room ID or Group UUID required'})
            return
        
        user_uuid = session.get('user_uuid')
        if not user_uuid:
            emit('error', {'message': 'Authentication required'})
            return
        
        try:
            # Определяем комнату
            if group_uuid:
                group = Group.query.filter_by(uuid=group_uuid).first()
                if not group:
                    emit('error', {'message': 'Group not found'})
                    return
                room = f'group_{group.id}'
            else:
                room = f'room_{room_id}'
            
            join_room(room)
            emit('room_joined', {
                'room': room,
                'message': f'Joined room: {room}'
            })
            
        except Exception as e:
            emit('error', {'message': f'Error joining room: {str(e)}'})

    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Выход из комнаты/группы"""
        room_id = data.get('room_id')
        group_uuid = data.get('group_uuid')
        
        if room_id:
            room = f'room_{room_id}'
            leave_room(room)
            emit('room_left', {
                'room': room,
                'message': f'Left room: {room}'
            })
        elif group_uuid:
            group = Group.query.filter_by(uuid=group_uuid).first()
            if group:
                room = f'group_{group.id}'
                leave_room(room)
                emit('room_left', {
                    'room': room,
                    'message': f'Left group: {group.name}'
                })

    @socketio.on('send_message')
    def handle_send_message(data):
        """Обработка отправки сообщения"""
        try:
            user_uuid = session.get('user_uuid')
            if not user_uuid:
                emit('message_error', {'error': 'Authentication required'})
                return
            
            user = User.query.filter_by(uuid=user_uuid).first()
            if not user:
                emit('message_error', {'error': 'User not found'})
                return
            
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            group_id = data.get('group_id')
            is_encrypted = data.get('is_encrypted', False)
            encryption_key = data.get('encryption_key')
            file_url = data.get('file_url')
            file_name = data.get('file_name')
            
            if not content and not file_url:
                emit('message_error', {'error': 'Message content or file is required'})
                return
            
            # Создание сообщения
            new_message = Message(
                content=content,
                message_type=message_type,
                user_id=user.id,
                group_id=group_id,
                is_encrypted=is_encrypted,
                encryption_key=encryption_key,
                file_url=file_url,
                file_name=file_name
            )
            
            db_instance.session.add(new_message)
            db_instance.session.commit()
            
            # Подготовка данных для отправки
            message_data = new_message.to_dict()
            
            # Отправка в комнату или всем
            if group_id:
                # Отправка в конкретную группу
                emit('new_message', message_data, room=f'group_{group_id}')
            else:
                # Отправка в общий чат
                emit('new_message', message_data, broadcast=True)
                
        except Exception as e:
            emit('message_error', {'error': f'Error sending message: {str(e)}'})

    @socketio.on('get_message_history')
    def handle_get_history(data):
        """Получение истории сообщений"""
        try:
            group_id = data.get('group_id')
            limit = min(data.get('limit', 50), 100)  # Максимум 100 сообщений
            offset = data.get('offset', 0)
            
            # Базовый запрос
            query = Message.query.join(User)
            
            if group_id:
                query = query.filter_by(group_id=group_id)
            else:
                query = query.filter_by(group_id=None)  # Общий чат
            
            # Получение сообщений
            messages = query.order_by(Message.created_at.desc())\
                          .limit(limit)\
                          .offset(offset)\
                          .all()
            
            messages_data = [msg.to_dict() for msg in reversed(messages)]
            
            emit('message_history', {
                'messages': messages_data,
                'group_id': group_id,
                'has_more': len(messages) == limit
            })
            
        except Exception as e:
            emit('error', {'message': f'Error getting history: {str(e)}'})

    @socketio.on('typing')
    def handle_typing(data):
        """Обработка индикатора набора текста"""
        user_uuid = session.get('user_uuid')
        if user_uuid:
            user = User.query.filter_by(uuid=user_uuid).first()
            if user:
                group_id = data.get('group_id')
                is_typing = data.get('is_typing', False)
                
                room = f'group_{group_id}' if group_id else None
                
                emit('user_typing', {
                    'user_id': user.id,
                    'username': user.username,
                    'is_typing': is_typing
                }, room=room, broadcast=True)

    @socketio.on('user_typing_stop')
    def handle_typing_stop(data):
        """Остановка индикатора набора текста"""
        user_uuid = session.get('user_uuid')
        if user_uuid:
            user = User.query.filter_by(uuid=user_uuid).first()
            if user:
                group_id = data.get('group_id')
                room = f'group_{group_id}' if group_id else None
                
                emit('user_typing', {
                    'user_id': user.id,
                    'username': user.username,
                    'is_typing': False
                }, room=room, broadcast=True)

# HTTP маршруты
@bp.route('/')
def index():
    """Главная страница чата"""
    # If user not authenticated server-side, redirect to login page
    if not session.get('user_uuid'):
        return redirect('/auth')
    return render_template('index.html')

@bp.route('/api/messages')
def get_messages():
    """API для получения истории сообщений (HTTP)"""
    try:
        group_id = request.args.get('group_id', type=int)
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        query = Message.query.join(User)
        
        if group_id:
            query = query.filter_by(group_id=group_id)
        else:
            query = query.filter_by(group_id=None)
        
        messages = query.order_by(Message.created_at.desc())\
                       .limit(limit)\
                       .offset(offset)\
                       .all()
        
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in reversed(messages)],
            'group_id': group_id,
            'has_more': len(messages) == limit
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/users/online')
def get_online_users():
    """API для получения списка онлайн пользователей"""
    try:
        online_users_list = []
        for sid, user_info in online_users.items():
            user = User.query.get(user_info['user_id'])
            if user:
                online_users_list.append(user.to_dict())
        
        return jsonify({
            'success': True,
            'online_users': online_users_list,
            'count': len(online_users_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/users')
def get_all_users():
    """API для получения всех пользователей"""
    try:
        users = User.query.order_by(User.username).all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500