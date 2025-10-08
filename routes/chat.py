from flask import Blueprint, render_template, request
from flask_socketio import emit, join_room, leave_room
from extensions import db, socketio
from models.message import Message, Group
from models.user import User
from datetime import datetime
import uuid

bp = Blueprint("chat", __name__, url_prefix="/chat")

# ==========================
#  ОТРИСОВКА СТРАНИЦЫ ЧАТА
# ==========================
@bp.route("/")
def index():
    return render_template("index.html")


# ==========================
#  SOCKET.IO ОБРАБОТЧИКИ
# ==========================
def init_socket_handlers(socketio, db):
    """Инициализация всех событий сокета"""

    # --- Подключение клиента ---
    @socketio.on("connect")
    def handle_connect():
        print(f"✅ Client connected: {request.sid}")
        emit("connected", {"message": "Connected to chat server"})

    @socketio.on("disconnect")
    def handle_disconnect():
        print(f"⚠️ Client disconnected: {request.sid}")

    # --- Авторизация пользователя ---
    @socketio.on("user_connected")
    def handle_user_connected(data):
        username = data.get("username")
        user_uuid = data.get("uuid")

        if not username or not user_uuid:
            emit("error", {"error": "Missing username or uuid"})
            return

        # Проверяем или создаем пользователя
        user = User.query.filter_by(uuid=user_uuid).first()
        if not user:
            user = User(uuid=user_uuid, username=username)
            db.session.add(user)
            db.session.commit()

        # Отправляем список групп при подключении
        groups = Group.query.all()
        emit("group_list", [g.to_dict() for g in groups])

    # --- Создание новой группы ---
    @socketio.on("create_group")
    def handle_create_group(data):
        name = data.get("name", "").strip()
        if not name:
            emit("error", {"error": "Имя группы обязательно"})
            return

        new_group = Group(
            uuid=str(uuid.uuid4()),
            name=name,
            description=data.get("description", ""),
            created_by=None
        )
        db.session.add(new_group)
        db.session.commit()

        emit("group_created", new_group.to_dict(), broadcast=True)

    # --- Присоединение к группе ---
    @socketio.on("join_group")
    def handle_join_group(data):
        group_id = data.get("group_id")
        if not group_id:
            emit("error", {"error": "Не указан ID группы"})
            return

        join_room(group_id)
        print(f"👥 User {request.sid} joined group {group_id}")

        messages = (
            Message.query.filter_by(group_id=group_id)
            .order_by(Message.timestamp.asc())
            .all()
        )
        emit("chat_history", [m.to_dict() for m in messages])

    # --- Отправка сообщения ---
    @socketio.on("send_message")
    def handle_send_message(data):
        text = data.get("text", "").strip()
        group_id = data.get("group_id")
        sender_name = data.get("sender")
        sender_uuid = data.get("uuid")

        if not text or not group_id or not sender_uuid:
            emit("error", {"error": "Неполные данные сообщения"})
            return

        user = User.query.filter_by(uuid=sender_uuid).first()
        if not user:
            user = User(uuid=sender_uuid, username=sender_name)
            db.session.add(user)
            db.session.commit()

        msg = Message(
            uuid=str(uuid.uuid4()),
            group_id=group_id,
            user_id=user.id,
            content=text,
            timestamp=datetime.utcnow()
        )
        db.session.add(msg)
        db.session.commit()

        payload = {
            "text": text,
            "sender": sender_name,
            "uuid": sender_uuid,
            "group_id": group_id,
            "timestamp": msg.timestamp.isoformat()
        }
        emit("new_message", payload, room=group_id)

    # --- Выход из группы ---
    @socketio.on("leave_group")
    def handle_leave_group(data):
        group_id = data.get("group_id")
        if not group_id:
            return
        leave_room(group_id)
        print(f"🚪 User {request.sid} left group {group_id}")
