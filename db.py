import os, sqlite3
from typing import Tuple
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

DEFAULT_DB_PATH = os.environ.get("DB_PATH", "data/serials.db")
TZ_NAME = os.environ.get("TZ", "Asia/Ho_Chi_Minh")

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def get_conn(db_path: str = DEFAULT_DB_PATH):
    ensure_dir(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS checks ("
        " code TEXT PRIMARY KEY,"
        " check_count INTEGER DEFAULT 0,"
        " last_checked_at TEXT,"
        " is_known INTEGER DEFAULT 0"
        ")"
    )
    conn.commit()
    return conn

def now_iso() -> str:
    try:
        if ZoneInfo:
            return datetime.now(ZoneInfo(TZ_NAME)).isoformat(timespec="seconds")
    except Exception:
        pass
    return datetime.now().isoformat(timespec="seconds")

def normalize(code: str) -> str:
    return (code or "").strip().upper().replace(" ", "")

def bump(code: str, is_known: bool, db_path: str = DEFAULT_DB_PATH) -> Tuple[int, str]:
    code_n = normalize(code)
    ts = now_iso()
    conn = get_conn(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO checks(code, check_count, last_checked_at, is_known) "
        "VALUES(?, 1, ?, ?) "
        "ON CONFLICT(code) DO UPDATE SET "
        "  check_count = checks.check_count + 1, "
        "  last_checked_at = excluded.last_checked_at, "
        "  is_known = CASE WHEN excluded.is_known=1 THEN 1 ELSE checks.is_known END",
        (code_n, ts, 1 if is_known else 0),
    )
    conn.commit()
    cur.execute("SELECT check_count, last_checked_at FROM checks WHERE code=?", (code_n,))
    row = cur.fetchone()
    return int(row[0] or 0), (row[1] or ts)
