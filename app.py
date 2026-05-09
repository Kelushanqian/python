# app.py
import os
import threading
import sqlite3
from flask import Flask

from config import ORIGINAL_DIR, PROCESSED_DIR, DB_PATH
from worker import worker_loop
from routes import bp

app = Flask(__name__)
app.register_blueprint(bp)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drone_id TEXT NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            capture_time TEXT NOT NULL,
            original_path TEXT NOT NULL,
            processed_path TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    os.makedirs(ORIGINAL_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    init_db()

    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))