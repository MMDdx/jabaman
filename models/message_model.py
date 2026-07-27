# models/message_model.py
"""توابع دامنه‌ی پیام‌های تماس با ما.

شامل:
- get_all_messages / get_message / create_message
- mark_message_read / delete_message
"""
from ._shared import get_db, _dict


def get_all_messages():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, fullname, email, phone, topic, message_text, is_read, created_at "
            "FROM messages ORDER BY id DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_message(message_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return _dict(row)


def create_message(fullname, email, phone, topic, message_text):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (fullname, email, phone, topic, message_text) "
            "VALUES (?, ?, ?, ?, ?)",
            (fullname, email, phone, topic, message_text)
        )
        conn.commit()


def mark_message_read(message_id, is_read=True):
    with get_db() as conn:
        conn.execute(
            "UPDATE messages SET is_read = ? WHERE id = ?",
            (1 if is_read else 0, message_id)
        )
        conn.commit()


def delete_message(message_id):
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        conn.commit()
