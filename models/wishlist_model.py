# models/wishlist_model.py
"""توابع دامنه‌ی علاقه‌مندی‌ها.

شامل:
- get_wishlist_items / add_to_wishlist / remove_from_wishlist
"""
from ._shared import get_db, _dict


def get_wishlist_items(user_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT w.id AS wishlist_id, p.id, p.title, p.location, p.price_per_night, p.images "
            "FROM wishlist w JOIN properties p ON w.property_id = p.id "
            "WHERE w.user_id = ? ORDER BY w.added_at DESC",
            (user_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def add_to_wishlist(user_id, property_id):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO wishlist (user_id, property_id) VALUES (?, ?)",
            (user_id, property_id)
        )
        conn.commit()


def remove_from_wishlist(user_id, wishlist_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM wishlist WHERE id = ? AND user_id = ?",
            (wishlist_id, user_id)
        )
        conn.commit()
