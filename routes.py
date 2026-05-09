# routes.py
# 路由接口
# 只负责：参数校验、调用业务函数、返回响应
# 文件存储 → storage.py，数据库操作 → database.py，帧抽取 → extract_frames.py

import threading
from flask import Blueprint, jsonify, request, send_from_directory
from database import insert_image, fetch_all_images
from storage import save_original_image, save_video
from extract_frames import extract_and_upload
import time

bp = Blueprint('main', __name__)


# POST /api/ingest 接收上传的图片，存档并写入数据库
@bp.route('/api/ingest', methods=['POST'])
def ingest():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    drone_id = request.form.get('drone_id', 'drone_unknown')
    x = request.form.get('x', 0)
    y = request.form.get('y', 0)

    try:
        original_path, _ = save_original_image(request.files['file'].read())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    insert_image(drone_id, x, y, time.strftime("%Y-%m-%d %H:%M:%S"), original_path)
    return jsonify({'status': 'ok', 'filename': original_path.split('/')[-1]})


# GET /api/images 返回所有图片记录（含处理状态）
@bp.route('/api/images', methods=['GET'])
def get_images():
    return jsonify(fetch_all_images())


# GET /images/<folder>/<filename> 访问图片文件
@bp.route('/images/<folder>/<filename>')
def serve_image(folder, filename):
    # 只允许访问 original 和 processed 两个目录，防止路径穿越
    allowed_folders = {'original', 'processed'}
    if folder not in allowed_folders:
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(f"images/{folder}", filename)


# POST /api/ingest_video 接收上传的视频，后台抽帧入库
@bp.route('/api/ingest_video', methods=['POST'])
def ingest_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    drone_id = request.form.get('drone_id', 'drone_unknown')
    x = request.form.get('x', 0)
    y = request.form.get('y', 0)
    interval_seconds = float(request.form.get('interval_seconds', 5))

    video_path = save_video(request.files['file'])

    threading.Thread(
        target=extract_and_upload,
        args=(video_path, interval_seconds, drone_id, x, y),
        daemon=True
    ).start()

    return jsonify({'status': 'ok', 'video': video_path.split('/')[-1]})