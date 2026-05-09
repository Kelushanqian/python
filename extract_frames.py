# extract_frames.py
# 视频帧抽取
# 直接调 storage 和 database，不再通过 HTTP 回调自身

import cv2
import time
from storage import save_original_image
from database import insert_image

def extract_and_upload(video_path, interval_seconds=1, drone_id="1", x=0, y=0):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"打不开视频：{video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print(f"无法读取帧率：{video_path}")
        cap.release()
        return

    frame_interval = int(fps * interval_seconds)
    frame_index = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            frame = cv2.resize(frame, (800, 800))
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                frame_index += 1
                continue

            try:
                original_path, _ = save_original_image(buffer.tobytes())
                insert_image(drone_id, x, y, time.strftime("%Y-%m-%d %H:%M:%S"), original_path)
                saved += 1
            except Exception as e:
                print(f"第 {frame_index} 帧保存失败：{e}")

        frame_index += 1

    cap.release()
    print(f"完成，共保存 {saved} 张")