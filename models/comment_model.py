# models/comment_model.py
"""توابع دامنه‌ی نظرات اقامتگاه‌ها.

شامل:
- get_comments_for_property / get_all_comments / get_comment
- add_comment / delete_comment
"""
from ._shared import get_db, _dict


def get_comments_for_property(property_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.comment_text, c.rating, c.created_at, "
            "       u.first_name || ' ' || u.last_name AS user_name "
            "FROM comments c JOIN users u ON c.user_id = u.id "
            "WHERE c.property_id = ? ORDER BY c.created_at DESC",
            (property_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_all_comments():
    """گرفتن همه‌ی نظرات (برای پنل ادمین) به‌همراه نام کاربر و عنوان اقامتگاه."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.id, c.user_id, c.property_id, c.comment_text, c.rating, c.created_at, "
            "       u.first_name || ' ' || u.last_name AS user_name, "
            "       p.title AS property_title "
            "FROM comments c "
            "JOIN users u ON c.user_id = u.id "
            "JOIN properties p ON c.property_id = p.id "
            "ORDER BY c.created_at DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_comment(comment_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM comments WHERE id = ?", (comment_id,)
        ).fetchone()
    return _dict(row)


def delete_comment(comment_id):
    with get_db() as conn:
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()


def add_comment(user_id, property_id, comment_text, rating):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO comments (user_id, property_id, comment_text, rating) "
            "VALUES (?, ?, ?, ?)",
            (user_id, property_id, comment_text, rating)
        )
        conn.commit()
