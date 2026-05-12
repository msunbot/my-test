"""
SQLite store for tracking seen articles and persisting digests.
"""
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime


def _hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


class ArticleStore:
    def __init__(self, db_path: str = "seen_articles.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init()

    def _init(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS seen (
                url_hash TEXT PRIMARY KEY,
                url      TEXT NOT NULL,
                seen_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS digests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                content    TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def is_seen(self, url: str) -> bool:
        h = _hash(url)
        row = self.conn.execute("SELECT 1 FROM seen WHERE url_hash=?", (h,)).fetchone()
        return row is not None

    def mark_seen(self, url: str):
        h = _hash(url)
        self.conn.execute(
            "INSERT OR IGNORE INTO seen(url_hash, url, seen_at) VALUES(?,?,?)",
            (h, url, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def save_digest(self, content: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO digests(created_at, content) VALUES(?,?)",
            (datetime.utcnow().isoformat(), content),
        )
        self.conn.commit()
        return cur.lastrowid

    def recent_digests(self, limit: int = 5) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, created_at, content FROM digests ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"id": r[0], "created_at": r[1], "content": r[2]} for r in rows]

    def close(self):
        self.conn.close()
