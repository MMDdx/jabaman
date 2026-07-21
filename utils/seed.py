# utils/seed.py
"""پر کردن دیتابیس با داده‌های نمونه برای تست.

تغییرات نسبت به نسخه‌ی قبل:
- کاربران با email ثبت می‌شوند (نه phone).
- از PBKDF2 برای هش رمز استفاده می‌شود.
- یک کاربر ادمین اضافه شده (برای دسترسی به /admin).
- مسیر DB مطلق است.
"""
import sys
import os

# اضافه‌کردن ریشه‌ی پروژه به sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import db_setup
from utils.security import hash_password

# تنظیم مسیر دیتابیس
db_setup.DB_NAME = os.path.join(BASE_DIR, "db.sqlite")


def seed():
    # ۱. ساخت/مهاجرت جداول
    db_setup.main()

    # ۲. اتصال به همان دیتابیس
    import sqlite3
    conn = sqlite3.connect(db_setup.DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # ۳. کاربران نمونه — حالا با ایمیل
    # is_admin به‌صورت Boolean (True/False) — در DB به‌صورت 0/1 ذخیره می‌شود
    users = [
        # (first, last, email, phone, password_hash, account_type, is_admin)
        ("علی", "محمدی", "ali@example.com", "09123456789", hash_password("12345678"), "host", False),
        ("مریم", "احمدی", "maryam@example.com", "09187654321", hash_password("87654321"), "guest", False),
        ("رضا", "کریمی", "reza@example.com", "09351234567", hash_password("password123"), "host", False),
        ("سارا", "نیکپور", "sara@example.com", "09121112222", hash_password("sara1234"), "guest", False),
        ("ادمین", "سیستم", "admin@example.com", "09120000000", hash_password("admin1234"), "host", True),
    ]
    # تبدیل bool به 0/1 برای SQLite
    users_for_db = [
        (f, l, e, p, ph, at, 1 if ia else 0)
        for (f, l, e, p, ph, at, ia) in users
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO users (first_name, last_name, email, phone, password, account_type, is_admin) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        users_for_db
    )

    # ۴. اقامتگاه‌های نمونه
    properties = [
        (1, "ویلای ساحلی رویایی", "ویلایی زیبا با منظره دریا", "villa", "مازندران", 1200000, 6, 3, 2, "wifi,parking,pool", "/static/images/villa1.jpg"),
        (3, "آپارتمان مدرن", "آپارتمانی در مرکز شهر", "apartment", "تهران", 850000, 4, 2, 1, "wifi,tv,air_conditioning", "/static/images/apart1.jpg"),
        (1, "کلبه جنگلی", "کلبه چوبی دنج", "cottage", "نور", 650000, 4, 2, 1, "parking,kitchen", "/static/images/cottage1.jpg"),
        (3, "پنت‌هاوس لوکس", "پنت‌هاوس با چشم‌انداز ۳۶۰", "penthouse", "الهیه", 2500000, 8, 4, 3, "wifi,pool,tv,washer", "/static/images/pent1.jpg"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO properties "
        "(host_id, title, description, property_type, location, price_per_night, "
        " max_guests, bedrooms, bathrooms, amenities, images) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        properties
    )

    # ۵. پیام‌های نمونه
    messages = [
        ("ناشناس", "test@mail.com", "09120000000", "feedback", "عالی هستید", 0),
        ("زهرا", "zahra@mail.com", "09135556677", "booking", "مشکل در رزرو", 0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO messages (fullname, email, phone, topic, message_text, is_read) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        messages
    )

    # ۶. سبد خرید و علاقه‌مندی
    cart_items = [(2, 1), (2, 3)]
    cursor.executemany("INSERT OR IGNORE INTO cart (user_id, property_id) VALUES (?,?)", cart_items)

    wishlist_items = [(2, 4), (2, 2)]
    cursor.executemany("INSERT OR IGNORE INTO wishlist (user_id, property_id) VALUES (?,?)", wishlist_items)

    # ۷. نظرات
    comments = [
        (2, 1, "اقامتگاه فوق‌العاده‌ای بود!", 5),
        (4, 1, "محیط آرام و تمیز", 4),
        (2, 2, "موقعیت مکانی عالی", 5),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO comments (user_id, property_id, comment_text, rating) "
        "VALUES (?, ?, ?, ?)",
        comments
    )

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("✅ داده‌های آزمایشی با موفقیت اضافه شدند.")
    print("=" * 60)
    print("\nحساب‌های کاربری تستی:")
    print("-" * 60)
    print(f"  ادمین   : admin@example.com  /  admin1234")
    print(f"  میزبان  : ali@example.com   /  12345678")
    print(f"  میزبان  : reza@example.com  /  password123")
    print(f"  مهمان   : maryam@example.com /  87654321")
    print(f"  مهمان   : sara@example.com  /  sara1234")
    print("-" * 60)


if __name__ == "__main__":
    seed()
