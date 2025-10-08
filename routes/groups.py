from flask import Blueprint, request, jsonify, session
from extensions import db
from models.user import User
from models.message import Message, Group
from datetime import datetime
import uuid

bp_groups = Blueprint('groups', __name__)


@bp_groups.route('/api/groups', methods=['GET'])
def get_groups():
    """Получить список всех групп"""
    try:
        groups = Group.query.all()
        return jsonify({
            'success': True,
            'groups': [g.to_dict() for g in groups]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp_groups.route('/api/groups/<uuid:group_uuid>', methods=['GET'])
def get_group(group_uuid):
    """Получить информацию о конкретной группе"""
    try:
        group = Group.query.filter_by(uuid=str(group_uuid)).first()
        if not group:
            return jsonify({'error': 'Группа не найдена'}), 404
        
        return jsonify({
            'success': True,
            'group': group.to_dict(),
            'members': [m.to_dict() for m in group.members]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp_groups.route('/api/groups', methods=['POST'])
def create_group():
    """Создание новой группы"""
    try:
        user_uuid = session.get('user_uuid')
        if not user_uuid:
            return jsonify({'error': 'Не авторизован'}), 401
        
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '')
        is_private = data.get('is_private', False)
        
        if not name:
            return jsonify({'error': 'Имя группы обязательно'}), 400
        
        creator = User.query.filter_by(uuid=user_uuid).first()
        if not creator:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Создаем группу
        new_group = Group(
            uuid=str(uuid.uuid4()),
            name=name,
            description=description,
            created_by=creator.id,
            is_private=is_private
        )
        db.session.add(new_group)
        db.session.commit()
        
        # Добавляем создателя как участника
        new_group.members.append(creator)
        db.session.commit()
        
        # Системное сообщение о создании группы
        system_message = Message(
            content=f'Группа "{new_group.name}" создана пользователем {creator.username}',
            message_type='system',
            user_id=creator.id,
            group_id=new_group.id
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'group': new_group.to_dict(),
            'message': f'Группа "{name}" успешно создана'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp_groups.route('/api/groups/<uuid:group_uuid>/join', methods=['POST'])
def join_group(group_uuid):
    """Присоединение пользователя к группе"""
    try:
        user_uuid = session.get('user_uuid')
        if not user_uuid:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.filter_by(uuid=user_uuid).first()
        group = Group.query.filter_by(uuid=str(group_uuid)).first()
        
        if not user or not group:
            return jsonify({'error': 'Пользователь или группа не найдены'}), 404
        
        if user in group.members:
            return jsonify({'message': 'Уже в группе'}), 200
        
        group.members.append(user)
        db.session.commit()
        
        # Системное сообщение о присоединении
        system_message = Message(
            content=f'{user.username} присоединился к группе "{group.name}"',
            message_type='system',
            user_id=user.id,
            group_id=group.id
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Пользователь {user.username} добавлен в группу "{group.name}"'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp_groups.route('/api/groups/<uuid:group_uuid>/leave', methods=['POST'])
def leave_group(group_uuid):
    """Покинуть группу"""
    try:
        user_uuid = session.get('user_uuid')
        if not user_uuid:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.filter_by(uuid=user_uuid).first()
        group = Group.query.filter_by(uuid=str(group_uuid)).first()
        
        if not user or not group:
            return jsonify({'error': 'Пользователь или группа не найдены'}), 404
        
        if user not in group.members:
            return jsonify({'message': 'Пользователь не состоит в группе'}), 400
        
        group.members.remove(user)
        db.session.commit()
        
        # Системное сообщение о выходе
        system_message = Message(
            content=f'{user.username} покинул группу "{group.name}"',
            message_type='system',
            user_id=user.id,
            group_id=group.id
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Пользователь {user.username} покинул группу "{group.name}"'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp_groups.route('/api/groups/<uuid:group_uuid>', methods=['DELETE'])
def delete_group(group_uuid):
    """Удалить группу"""
    try:
        user_uuid = session.get('user_uuid')
        if not user_uuid:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.filter_by(uuid=user_uuid).first()
        group = Group.query.filter_by(uuid=str(group_uuid)).first()
        
        if not user or not group:
            return jsonify({'error': 'Пользователь или группа не найдены'}), 404
        
        if group.created_by != user.id:
            return jsonify({'error': 'Только создатель может удалить группу'}), 403
        
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Группа "{group.name}" удалена'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
