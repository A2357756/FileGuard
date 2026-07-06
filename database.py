import sqlite3

DB_FILE = "guardian.db"

def init_db():
    #連結到"guardian.db"資料庫，如果不存在則會自動建立
    conn = sqlite3.connect(DB_FILE)
    #連線到資料庫後，建立一個cursor物件，用來執行SQL語句
    cursor = conn.cursor()
    #建立events資料表，如果表存在就跳過。
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            path TEXT NOT NULL,
            event_type TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            last_seen TEXT NOT NULL
        )
    """)
    #SQL寫入
    conn.commit()
    #關閉連線
    conn.close()

def log_event(path, event_type):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        #?佔位符，安全寫入，避免SQL注入攻擊
        "INSERT INTO events (timestamp, path, event_type) VALUES (datetime('now', 'localtime'), ?, ?)",
        (path, event_type)
    )
    conn.commit()
    conn.close()

def get_baseline():
    """讀取目前資料庫裡所有檔案的 hash,格式跟原本的 baseline.json 一樣是字典"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT path, sha256 FROM files")
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)  # 把 [(path, hash), ...] 轉成 {path: hash, ...}

def update_file(path, sha256):
    """新增或更新一筆檔案的 hash 記錄"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO files (path, sha256, last_seen)
        VALUES (?, ?, datetime('now', 'localtime'))
        ON CONFLICT(path) DO UPDATE SET
            sha256 = excluded.sha256,
            last_seen = excluded.last_seen
    """, (path, sha256))
    conn.commit()
    conn.close()