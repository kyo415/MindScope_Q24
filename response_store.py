"""Lưu khảo sát Q24 có chọn tham gia vào SQLite cục bộ.

Không lưu thông tin nhận diện, địa chỉ IP hoặc user agent.
Chỉ tạo database khi người dùng đồng ý lưu. Mã biên nhận bí mật được băm
trước khi ghi xuống đĩa. Mặc định xóa dữ liệu sau 30 ngày khi DB được truy cập.

CẢNH BÁO: SQLite không mã hóa trên ổ đĩa; chỉ dùng máy cá nhân localhost.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'database' / 'q24_responses.sqlite3'
RETENTION_DAYS = 30


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=8)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA busy_timeout=8000')
    connection.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            country TEXT NOT NULL,
            answers_json TEXT NOT NULL,
            predicted_code INTEGER NOT NULL CHECK(predicted_code IN (1,2)),
            model_score_yes REAL NOT NULL
        )
    ''')
    return connection


def _hash_receipt(receipt: str) -> str:
    return hashlib.sha256(receipt.encode('utf-8')).hexdigest()


def _clean_expired(conn: sqlite3.Connection) -> None:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    conn.execute('DELETE FROM responses WHERE created_at < ?', (cutoff,))


def save_response(country: str, answers: dict[str, int], result: dict) -> str:
    receipt = secrets.token_urlsafe(32)
    with _connect() as conn:
        _clean_expired(conn)
        conn.execute('''
            INSERT INTO responses
              (receipt_hash, created_at, country, answers_json, predicted_code, model_score_yes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            _hash_receipt(receipt), datetime.now(timezone.utc).isoformat(), country,
            json.dumps(answers, ensure_ascii=False, separators=(',', ':')),
            result['predicted_code'], result['model_score_yes']
        ))
    return receipt


def retrieve_response(receipt: str) -> dict | None:
    if not DB_PATH.is_file():
        return None
    with _connect() as conn:
        _clean_expired(conn)
        row = conn.execute('''SELECT created_at, country, answers_json, predicted_code,
                                     model_score_yes FROM responses WHERE receipt_hash = ?''',
                           (_hash_receipt(receipt),)).fetchone()
    if not row:
        return None
    return {
        'created_at': row['created_at'], 'country': row['country'],
        'answers': json.loads(row['answers_json']),
        'predicted_code': row['predicted_code'],
        'predicted_label': 'Có' if row['predicted_code'] == 1 else 'Không',
        'model_score_yes': row['model_score_yes'],
    }


def delete_response(receipt: str) -> bool:
    if not DB_PATH.is_file():
        return False
    with _connect() as conn:
        _clean_expired(conn)
        row = conn.execute('DELETE FROM responses WHERE receipt_hash = ?',
                           (_hash_receipt(receipt),))
        return row.rowcount > 0
