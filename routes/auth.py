from flask import Blueprint, request, jsonify, session, render_template
from extensions import db
from models.user import User
import uuid

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/auth', methods=['GET'])
def auth_page():
    """Render the login/registration page"""
    return render_template('login.html')

@bp_auth.route('/auth/join', methods=['POST'])
def join_chat():
    """Простая авторизация по UUID и кодовому слову"""
    data = request.get_json()
    
    if not data or 'codeword' not in data:
        return jsonify({'error': 'Кодовое слово обязательно'}), 400
    
    codeword = data.get('codeword', '').strip()
    username = data.get('username', '').strip() or f'User_{uuid.uuid4().hex[:8]}'
    user_uuid = data.get('uuid', '')  # Если передан существующий UUID
    
    if not codeword:
        return jsonify({'error': 'Кодовое слово не может быть пустым'}), 400
    
    try:
        if user_uuid:
            # Поиск существующего пользователя
            user = User.query.filter_by(uuid=user_uuid).first()
            if user and user.codeword == codeword:
                user.username = username or user.username
                user.is_online = True
                db.session.commit()
                
                session['user_uuid'] = user.uuid
                session['user_id'] = user.id
                
                return jsonify({
                    'success': True,
                    'user': user.to_dict(),
                    'message': 'Добро пожаловать обратно!'
                })
            else:
                return jsonify({'error': 'Неверный UUID или кодовое слово'}), 401
        
        # Создание нового пользователя
        new_user = User(
            codeword=codeword,
            username=username,
            is_online=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        session['user_uuid'] = new_user.uuid
        session['user_id'] = new_user.id
        
        return jsonify({
            'success': True,
            'user': new_user.to_dict(),
            'message': 'Новый пользователь создан!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@bp_auth.route('/auth/me', methods=['GET'])
def get_current_user():
    """Получить текущего пользователя"""
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'error': 'Не авторизован'}), 401
    
    user = User.query.filter_by(uuid=user_uuid).first()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify({'user': user.to_dict()})

@bp_auth.route('/auth/logout', methods=['POST'])
def logout():
    """Выход из системы"""
    user_uuid = session.get('user_uuid')
    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            user.is_online = False
            db.session.commit()
    
    session.clear()
    return jsonify({'success': True, 'message': 'Выход выполнен'})