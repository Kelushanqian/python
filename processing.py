# processing.py
# 图片处理逻辑

import cv2
import numpy as np
from mobile_sam import sam_model_registry, SamPredictor

_sam_predictor = None

# 加载 SAM 模型
def get_sam_predictor():
    global _sam_predictor
    if _sam_predictor is None:
        sam = sam_model_registry["vit_t"](checkpoint="mobile_sam.pt")
        sam.eval()
        _sam_predictor = SamPredictor(sam)
    return _sam_predictor

# 分割
def get_leaf_mask(img):
    predictor = get_sam_predictor()
    predictor.set_image(img)

    h, w = img.shape[:2]
    cx, cy = w // 2, h // 2

    center_points = np.array([
        [cx, cy],
        [cx, cy - h // 4],
        [cx, cy + h // 4],
        [cx - w // 4, cy],
        [cx + w // 4, cy],
    ])
    center_labels = np.array([1, 1, 1, 1, 1])

    masks, _, _ = predictor.predict(
        point_coords=center_points,
        point_labels=center_labels,
        multimask_output=False
    )
    return masks[0].astype(np.uint8)

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
    # 亮度
    if brightness < 80:
        clip_limit = 4.0
    elif brightness < 130:
        clip_limit = 3.0
    else:
        clip_limit = 2.0

    # 锐化
    if contrast < 30:
        sharpen_strength = 0.3
    elif contrast < 50:
        sharpen_strength = 0.2
    else:
        sharpen_strength = 0.1

    # 饱和度
    if saturation > 100:
        sat_scale = 1.1
    elif saturation > 60:
        sat_scale = 1.3
    else:
        sat_scale = 1.5

    return clip_limit, sharpen_strength, sat_scale

# 去噪
def apply_denoise(img):
    return cv2.bilateralFilter(img, 5, 50, 50)

# 亮度
def apply_clahe(img, clip_limit=3.0):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)

    merged = cv2.merge([l_enhanced, a, b])
    result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return result

# 对比度
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

    img = apply_denoise(img) # 去噪
    mask = get_leaf_mask(img) # 蒙版

    brightness, contrast, saturation = analyze_image(img) # 亮度、对比度、锐化
    clip_limit, sharpen_strength, sat_scale = get_adaptive_params(brightness, contrast, saturation)

    enhanced = apply_clahe(img, clip_limit=clip_limit) # 亮度
    enhanced = apply_hsv_enhancement(enhanced, saturation_scale=sat_scale) # 对比度
    enhanced = apply_sharpen(enhanced, strength=sharpen_strength) # 锐化

    mask_3ch = np.stack([mask, mask, mask], axis=2)
    blurred_bg = cv2.GaussianBlur(img, (51, 51), 0) # 模糊背景
    result = np.where(mask_3ch == 1, enhanced, blurred_bg)

    return result