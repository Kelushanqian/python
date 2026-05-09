# config.py
# 路径和目录

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH      = os.path.join(BASE_DIR, "data.db")
ORIGINAL_DIR = os.path.join(BASE_DIR, "images", "original")
PROCESSED_DIR = os.path.join(BASE_DIR, "images", "processed")