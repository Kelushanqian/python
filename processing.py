# processing.py
# 图片处理逻辑

import cv2
import numpy as np
from ultralytics import YOLO
from mobile_sam import sam_model_registry, SamPredictor

_yolo_model = None

# 加载 YOLO 模型
def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLO("best.onnx", task="detect")
    return _yolo_model

# YOLO 检测，返回 [{'box': [x1,y1,x2,y2], 'conf': float, 'cls': int}, ...]
def detect_diseases(img):
    model = get_yolo_model()
    results = model(img)
    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append({
            "box": [x1, y1, x2, y2],
            "conf": float(box.conf[0]),
            "cls": int(box.cls[0]),
        })
    return detections

# 分割
def get_leaf_mask(img, boxes=None):
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    if boxes:
        for x1, y1, x2, y2 in boxes:
            mask[int(y1):int(y2), int(x1):int(x2)] = 1
    else:
        mask[:] = 1  # 没检测到就全图当前景
    return mask

def analyze_image(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, _, _ = cv2.split(lab)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, _ = cv2.split(hsv)

    brightness = float(np.mean(l))
    contrast = float(np.std(l))
    saturation = float(np.mean(s))

    return brightness, contrast, saturation

def get_adaptive_params(brightness, contrast, saturation):
    if brightness < 80:
        clip_limit = 4.0
    elif brightness < 130:
        clip_limit = 3.0
    else:
        clip_limit = 2.0

    if contrast < 30:
        sharpen_strength = 0.3
    elif contrast < 50:
        sharpen_strength = 0.2
    else:
        sharpen_strength = 0.1

    if saturation > 100:
        sat_scale = 1.1
    elif saturation > 60:
        sat_scale = 1.3
    else:
        sat_scale = 1.5

    return clip_limit, sharpen_strength, sat_scale

# 去噪
def apply_denoise(img):
    return cv2.bilateralFilter(img, 5, 75, 75)

# 亮度
def apply_clahe(img, clip_limit=3.0):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    merged = cv2.merge([l_enhanced, a, b])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

# 饱和度
def apply_hsv_enhancement(img, saturation_scale=1.3):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = np.clip(s.astype(np.float32) * saturation_scale, 0, 255).astype(np.uint8)
    merged = cv2.merge([h, s, v])
    return cv2.cvtColor(merged, cv2.COLOR_HSV2BGR)

# 锐化
def apply_sharpen(img, strength=0.1):
    blurred = cv2.GaussianBlur(img, (0, 0), 3)
    return cv2.addWeighted(img, 1 + strength, blurred, -strength, 0)

def process_image_file(original_path):
    img = cv2.imread(original_path)
    if img is None:
        return None

    img_for_detect = apply_denoise(img)
    img_for_detect = apply_clahe(img_for_detect, clip_limit=2.0)

    # YOLO 检测
    detections = detect_diseases(img_for_detect)
    boxes = [d["box"] for d in detections]

    # 分割
    mask = get_leaf_mask(img, boxes=boxes if boxes else None)

    brightness, contrast, saturation = analyze_image(img)
    clip_limit, sharpen_strength, sat_scale = get_adaptive_params(brightness, contrast, saturation)

    enhanced = apply_clahe(img, clip_limit=clip_limit)
    enhanced = apply_sharpen(enhanced, strength=sharpen_strength)
    enhanced = apply_hsv_enhancement(enhanced, saturation_scale=sat_scale)

    mask_3ch = np.stack([mask, mask, mask], axis=2)
    blurred_bg = cv2.GaussianBlur(img, (51, 51), 0)
    result = np.where(mask_3ch == 1, enhanced, blurred_bg)

    # 画 YOLO 检测框
    for d in detections:
        x1, y1, x2, y2 = [int(v) for v in d["box"]]
        conf = d["conf"]
        cv2.rectangle(result, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(
            result,
            f"wanyi {conf:.2f}",
            (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    return result