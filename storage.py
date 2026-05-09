# storage.py
# 文件存储管理
# 负责图片和视频的保存、路径生成

import os
import time
import cv2
import numpy as np
from config import ORIGINAL_DIR, PROCESSED_DIR

def save_original_image(file_bytes: bytes) -> tuple[str, np.ndarray]:
    """
    接收图片并保存到 ORIGINAL_DIR。
    """
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片，可能不是有效的图片文件")

    filename = f"{int(time.time() * 1000)}.jpg"
    path = os.path.join(ORIGINAL_DIR, filename)
    cv2.imwrite(path, img)
    return path, img

def save_processed_image(img: np.ndarray, original_path: str) -> str:
    """
    将处理后的图片保存到 PROCESSED_DIR。
    """
    filename = os.path.basename(original_path)
    path = os.path.join(PROCESSED_DIR, filename)
    cv2.imwrite(path, img)
    return path

def save_video(file_storage) -> str:
    """
    保存视频到 videos/ 目录。
    """
    videos_dir = "videos"
    os.makedirs(videos_dir, exist_ok=True)
    filename = f"{int(time.time() * 1000)}.mp4"
    path = os.path.join(videos_dir, filename)
    file_storage.save(path)
    return path