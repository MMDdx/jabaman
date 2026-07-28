"""
شامل:
- SESSION_TTL_HOURS (ثابت)
- secrets_safe_uuid (helper داخلی)
- create_session / get_user_by_session / delete_session
"""
import secrets
from datetime import datetime, timedelta

from ._shared import get_db


SESSION_TTL_HOURS = 24


def secrets_safe_uuid():
    """تولید UUID امن با secrets (به‌جای uuid.uuid4 که امن نیست)."""
    return str(secrets.token_hex(16))


def create_session(user_id):
    session_id = secrets_safe_uuid()
    expires_at = (datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
            (session_id, user_id, expires_at)
        )
        conn.commit()
    return session_id


def get_user_by_session(session_id):
    """بررسی نشست و بازگرداندن user_id در صورت معتبر بودن."""
    if not session_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id, expires_at FROM sessions WHERE id = ?",
            (session_id,)
        ).fetchone()
    if not row:
        return None
    # بررسی انقضا
    if row["expires_at"]:
        try:
            expires = datetime.fromisoformat(row["expires_at"])
            if datetime.utcnow() > expires:
                delete_session(session_id)
                return None
        except ValueError:
            return None
    return row["user_id"]


def delete_session(session_id):
    if not session_id:
        return
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
