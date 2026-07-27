# models/user_model.py
"""توابع دامنه‌ی کاربران — مدیریت کاربران، نقش‌ها و دسترسی.

شامل:
- get_user / get_all_users / get_user_by_email
- create_user / update_user / delete_user
- is_admin / is_host / get_user_account_type
"""
from ._shared import get_db, _dict


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


def delete_user(user_id):
    """حذف کاربر — به‌خاطر ON DELETE CASCADE در جداول وابسته،
    اقامتگاه‌ها، نظرات، سبد و علاقه‌مندی‌های او هم حذف می‌شوند.
    """
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
