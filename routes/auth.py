from flask import Blueprint, request, jsonify, session, render_template
from extensions import db
from models.user import User
import uuid
import hashlib

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


# === Страница авторизации ===
@bp_auth.route("/", methods=["GET"])
def auth_page():
    """Возвращает страницу входа"""
    return render_template("login.html")


# === Авторизация или регистрация ===
@bp_auth.route("/join", methods=["POST"])
def join_chat():
    """
    Авторизация по UUID и кодовому слову с хешированием.
    Если пользователь существует — входит, иначе создаёт нового.
    """
    data = request.get_json() or {}

    codeword = data.get("codeword", "").strip()
    username = data.get("username", "").strip()
    user_uuid = data.get("uuid", "").strip()

    if not codeword:
        return jsonify({"success": False, "error": "Кодовое слово обязательно"}), 400

    if not username and not user_uuid:
        return jsonify({"success": False, "error": "Имя пользователя обязательно для регистрации"}), 400

    try:
        # === Попытка входа с существующим UUID ===
        if user_uuid:
            user = User.query.filter_by(uuid=user_uuid).first()
            if not user:
                return jsonify({"success": False, "error": "Пользователь не найден"}), 404
            
            # Проверяем кодовое слово через метод модели
            if not user.check_codeword(codeword):
                return jsonify({"success": False, "error": "Неверное кодовое слово"}), 401

            # Обновляем имя пользователя, если предоставлено и оно уникально
            if username and username != user.username:
                existing_user = User.query.filter_by(username=username).first()
                if existing_user and existing_user.uuid != user_uuid:
                    return jsonify({"success": False, "error": "Имя пользователя уже занято"}), 400
                user.username = username

            user.touch()
            db.session.commit()

            _store_user_session(user)
            return jsonify({
                "success": True,
                "user": user.to_dict(),
                "message": "Добро пожаловать обратно!"
            })

        # === Создание нового пользователя ===
        # Проверяем, не занято ли имя пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"success": False, "error": "Имя пользователя уже занято"}), 400

        # Создаем нового пользователя
        new_user = User(username=username)
        new_user.set_codeword(codeword)  # Устанавливаем хеш кодового слова
        new_user.is_online = True
        
        db.session.add(new_user)
        db.session.commit()

        _store_user_session(new_user)

        return jsonify({
            "success": True,
            "user": new_user.to_dict(),
            "message": "Новый пользователь создан!"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Ошибка сервера: {str(e)}"}), 500


# === Текущий пользователь ===
@bp_auth.route("/me", methods=["GET"])
def get_current_user():
    """Получить текущего пользователя по сессии"""
    user_uuid = session.get("user_uuid")
    if not user_uuid:
        return jsonify({"success": False, "error": "Не авторизован"}), 401

    user = User.query.filter_by(uuid=user_uuid).first()
    if not user:
        session.clear()
        return jsonify({"success": False, "error": "Пользователь не найден"}), 404

    user.touch()
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()})


# === Выход ===
@bp_auth.route("/logout", methods=["POST"])
def logout():
    """Выход из системы"""
    user_uuid = session.get("user_uuid")

    if user_uuid:
        user = User.query.filter_by(uuid=user_uuid).first()
        if user:
            user.logout()
            db.session.commit()

    session.clear()
    return jsonify({"success": True, "message": "Выход выполнен"})


# === Вспомогательная функция ===
def _store_user_session(user: User):
    """Сохранить пользователя в сессии"""
    session["user_uuid"] = user.uuid
    session["user_id"] = user.id
    session.permanent = True