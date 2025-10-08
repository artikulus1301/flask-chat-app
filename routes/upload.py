import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import uuid

bp_upload = Blueprint("upload", __name__)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "zip", "mp3", "mp4"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp_upload.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Нет файла"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Файл не выбран"}), 400

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename)
        file.save(full_path)

        file_url = f"/{UPLOAD_FOLDER}/{filename}"
        return jsonify({"url": file_url}), 200

    return jsonify({"error": "Неверный формат файла"}), 400
