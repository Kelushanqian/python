# database.py
# 数据库操作

import os
import sqlite3
from config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def insert_image(drone_id, x, y, capture_time, original_path):
    conn = get_db()
    conn.execute(
        "INSERT INTO images (drone_id, x, y, capture_time, original_path, status) VALUES (?, ?, ?, ?, ?, 'pending')",
        (drone_id, x, y, capture_time, original_path)
    )
    conn.commit()
    conn.close()

def fetch_pending():
    conn = get_db()
    row = conn.execute(
        "SELECT id, original_path FROM images WHERE status = 'pending' LIMIT 1"
    ).fetchone()
    conn.close()
    return row

def update_status(image_id, status, processed_path=None):
    conn = get_db()
    if processed_path:
        conn.execute(
            "UPDATE images SET status = ?, processed_path = ? WHERE id = ?",
            (status, processed_path, image_id)
        )
    else:
        conn.execute(
            "UPDATE images SET status = ? WHERE id = ?",
            (status, image_id)
        )
    conn.commit()
    conn.close()

def fetch_all_images():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, drone_id, x, y, capture_time, original_path, processed_path, status FROM images ORDER BY id DESC"
    ).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d['original_filename'] = os.path.basename(d['original_path']) if d['original_path'] else None
        d['processed_filename'] = os.path.basename(d['processed_path']) if d['processed_path'] else None
        result.append(d)
    return result

def fetch_image_id_by_path(original_path):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM images WHERE original_path = ? ORDER BY id DESC LIMIT 1",
        (original_path,)
    ).fetchone()
    conn.close()
    return row["id"] if row else None