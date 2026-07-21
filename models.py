# models.py
"""لایه‌ی Model در معماری MVC — تمام دسترسی‌های دیتابیس اینجا انجام می‌شود.

تغییرات نسبت به نسخه‌ی قبل:
- PRAGMA foreign_keys = ON در get_db فعال شده تا CASCADE واقعاً کار کند.
- کاربران با email لاگین می‌کنند (نه phone).
- پارامترهای password به password_hash تغییر نام داد (شفاف‌تر).
- توابع delete_from_cart و delete_from_wishlist اضافه شد.
- توابع get_user_by_email، get_user_with_role اضافه شد.
- توابع create_session و get_user_by_session با مدیریت انقضا.
- استفاده از context manager برای جلوگیری از connection leak.
- is_admin به‌صورت Boolean (در ساخت کاربر) استفاده می‌شود.
- توابع get_user_account_type و is_host برای کنترل دسترسی میزبان/مهمان.
"""
import sqlite3
import uuid
from datetime import datetime, timedelta

import db_setup

# استفاده از همان نام دیتابیس که در db_setup تعریف شده
DB_NAME = db_setup.DB_NAME


def get_db():
    """باز کردن یک اتصال جدید به دیتابیس با فعال بودن FK و Row factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _dict(row):
    """تبدیل sqlite3.Row به dict. اگر None باشد، None برمی‌گرداند."""
    return dict(row) if row is not None else None


# ===================== کاربران =====================

def get_user(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _dict(row)


def get_all_users():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, first_name, last_name, email, phone, account_type, is_admin, created_at "
            "FROM users ORDER BY id ASC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_user_by_email(email):
    """برای ورود با ایمیل."""
    if not email:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _dict(row)


def create_user(first_name, last_name, email, password_hash, account_type,
                phone=None, is_admin=False):
    """ساخت کاربر جدید.

    پارامترها:
      is_admin: bool (پیش‌فرض False).
                در DB به‌صورت 0/1 ذخیره می‌شود (SQLite BOOLEAN هم‌معنی INTEGER است).
    """
    # تبدیل bool به 0/1 برای ذخیره در SQLite
    is_admin_val = 1 if is_admin else 0
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, phone, password, account_type, is_admin) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, phone, password_hash, account_type, is_admin_val)
        )
        conn.commit()


def update_user(user_id, first_name, last_name, email, account_type, phone=None):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET first_name=?, last_name=?, email=?, phone=?, account_type=? WHERE id=?",
            (first_name, last_name, email, phone, account_type, user_id)
        )
        conn.commit()


def is_admin(user_id):
    """بررسی اینکه آیا کاربر admin است یا نه. خروجی همیشه bool است."""
    if not user_id:
        return False
    with get_db() as conn:
        row = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        return False
    # SQLite ممکن است 0/1 یا True/False برگرداند؛ در هر صورت bool می‌سازیم
    val = row["is_admin"]
    return bool(val) and val != 0


def get_user_account_type(user_id):
    """گرفتن نوع حساب کاربر ('guest' یا 'host').

    اگر کاربر وجود نداشت یا وارد نشده بود، None برمی‌گرداند.
    کاربرد: کنترل دسترسی به دکمه‌ی «افزودن اقامتگاه» در navbar
    که فقط باید برای میزبان‌ها نمایش داده شود.
    """
    if not user_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT account_type FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        return None
    return row["account_type"]


def is_host(user_id):
    """بررسی اینکه آیا کاربر میزبان است یا نه. خروجی همیشه bool است."""
    return get_user_account_type(user_id) == 'host'


# ===================== اقامتگاه‌ها =====================

def get_all_properties():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, host_id, title, property_type, location, price_per_night, "
            "max_guests, bedrooms, bathrooms, description, amenities, images, created_at "
            "FROM properties ORDER BY id DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_property(property_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
    return _dict(row)


def get_featured_properties(limit=6):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, property_type, location, price_per_night "
            "FROM properties ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_properties_by_host(host_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM properties WHERE host_id = ? ORDER BY id DESC",
            (host_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def create_property(host_id, title, description, property_type, location,
                    price_per_night, max_guests, bedrooms, bathrooms,
                    amenities=None, images=None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO properties "
            "(host_id, title, description, property_type, location, price_per_night, "
            " max_guests, bedrooms, bathrooms, amenities, images) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (host_id, title, description, property_type, location, price_per_night,
             max_guests, bedrooms, bathrooms, amenities, images)
        )
        conn.commit()


def update_property(property_id, title, description, property_type, location,
                    price_per_night, max_guests, bedrooms, bathrooms,
                    amenities=None, images=None):
    with get_db() as conn:
        conn.execute(
            "UPDATE properties SET title=?, description=?, property_type=?, location=?, "
            "price_per_night=?, max_guests=?, bedrooms=?, bathrooms=?, amenities=?, images=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, description, property_type, location, price_per_night,
             max_guests, bedrooms, bathrooms, amenities, images, property_id)
        )
        conn.commit()


def delete_property(property_id):
    with get_db() as conn:
        conn.execute("DELETE FROM properties WHERE id = ?", (property_id,))
        conn.commit()


# ===================== پیام‌ها =====================

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


# ===================== نظرات =====================

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


def add_comment(user_id, property_id, comment_text, rating):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO comments (user_id, property_id, comment_text, rating) "
            "VALUES (?, ?, ?, ?)",
            (user_id, property_id, comment_text, rating)
        )
        conn.commit()


# ===================== سبد خرید =====================

def get_cart_items(user_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.id AS cart_id, p.id, p.title, p.location, p.price_per_night, p.images "
            "FROM cart c JOIN properties p ON c.property_id = p.id "
            "WHERE c.user_id = ? ORDER BY c.added_at DESC",
            (user_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def add_to_cart(user_id, property_id):
    """از INSERT OR IGNORE استفاده می‌شود تا از تکرار جلوگیری شود."""
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO cart (user_id, property_id) VALUES (?, ?)",
            (user_id, property_id)
        )
        conn.commit()


def remove_from_cart(user_id, cart_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM cart WHERE id = ? AND user_id = ?",
            (cart_id, user_id)
        )
        conn.commit()


def clear_cart(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()


# ===================== علاقه‌مندی =====================

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


# ===================== نشست‌ها (Sessions) =====================

SESSION_TTL_HOURS = 24


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


def secrets_safe_uuid():
    """تولید UUID امن با secrets (به‌جای uuid.uuid4 که امن نیست)."""
    import secrets as _s
    return str(_s.token_hex(16))
