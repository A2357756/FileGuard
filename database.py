import sqlite3
import os
import platform

def get_app_data_dir():
    system = platform.system()
    if system == "Windows":
        base = os.getenv("APPDATA")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "FileGuard")

APP_DATA_DIR = get_app_data_dir()
os.makedirs(APP_DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(APP_DATA_DIR, "guardian.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            path TEXT NOT NULL,
            event_type TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            folder TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            PRIMARY KEY (folder, path)
        )
    """)
    conn.commit()
    conn.close()

def log_event(folder, path, event_type):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (folder, timestamp, path, event_type) VALUES (?, datetime('now', 'localtime'), ?, ?)",
        (folder, path, event_type)
    )
    conn.commit()
    conn.close()

def get_baseline(folder):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT path, sha256 FROM files WHERE folder = ?", (folder,))
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)

def update_file(folder, path, sha256):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO files (folder, path, sha256, last_seen)
        VALUES (?, ?, ?, datetime('now', 'localtime'))
        ON CONFLICT(folder, path) DO UPDATE SET
            sha256 = excluded.sha256,
            last_seen = excluded.last_seen
    """, (folder, path, sha256))
    conn.commit()
    conn.close()

def delete_file(folder, path):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE folder = ? AND path = ?", (folder, path))
    conn.commit()
    conn.close()

def get_events_since(folder, start_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, path, event_type FROM events WHERE folder = ? AND timestamp >= ? ORDER BY id",
        (folder, start_time)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_files_for_folder(folder):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE folder = ?", (folder,))
    conn.commit()
    conn.close()