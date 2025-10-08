import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

bp_upload = Blueprint("upload", __name__)

# Настройки
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "zip", "mp3", "mp4"}

def allowed_file(filename):
    """Проверяем, допустимо ли расширение файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp_upload.route("/upload", methods=["POST"])
def upload_file():
    """Обработчик загрузки файлов"""
    if "file" not in request.files:
        return jsonify({"error": "Нет файла в запросе"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Файл не выбран"}), 400

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        safe_name = secure_filename(f"{uuid.uuid4().hex}.{ext}")

        # Путь к директории загрузок
        upload_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(upload_dir, exist_ok=True)

        # Сохраняем файл
        file_path = os.path.join(upload_dir, safe_name)
        file.save(file_path)

        # Генерируем URL (для клиента)
        file_url = f"/{UPLOAD_FOLDER}/{safe_name}"

        return jsonify({
            "success": True,
            "url": file_url,
            "filename": safe_name,
            "message": "Файл успешно загружен"
        }), 200

    return jsonify({"error": "Недопустимый формат файла"}), 400
