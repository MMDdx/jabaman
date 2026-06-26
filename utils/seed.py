# utils/seed.py
import sys
import os
from hashlib import sha256

# ریشهٔ پروژه (پوشهٔ بالایی utils)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import db_setup

# تنظیم مسیر مطلق دیتابیس، تا عملیات در ریشهٔ پروژه انجام شود
db_setup.DB_NAME = os.path.join(BASE_DIR, "db.sqlite")

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def seed():
    # ۱. ساخت/به‌روزرسانی جداول با استفاده از db_setup
    db_setup.main()

    # ۲. اتصال به همان دیتابیس
    import sqlite3
    conn = sqlite3.connect(db_setup.DB_NAME)
    cursor = conn.cursor()

    # ۳. درج داده‌های نمونه
    users = [
        ("علی", "محمدی", "09123456789", hash_password("12345678"), "host"),
        ("مریم", "احمدی", "09187654321", hash_password("87654321"), "guest"),
        ("رضا", "کریمی", "09351234567", hash_password("password"), "host"),
        ("سارا", "نیکپور", "09121112222", hash_password("sara1234"), "guest"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO users (first_name, last_name, phone, password, account_type) VALUES (?,?,?,?,?)",
        users
    )

    properties = [
        (1, "ویلای ساحلی رویایی", "ویلایی زیبا با منظره دریا", "villa", "مازندران", 1200000, 6, 3, 2, "wifi,parking,pool", "/images/villa1.jpg"),
        (3, "آپارتمان مدرن", "آپارتمانی در مرکز شهر", "apartment", "تهران", 850000, 4, 2, 1, "wifi,tv,ac", "/images/apart1.jpg"),
        (1, "کلبه جنگلی", "کلبه چوبی دنج", "cottage", "نور", 650000, 4, 2, 1, "parking,kitchen", "/images/cottage1.jpg"),
        (3, "پنت‌هاوس لوکس", "پنت‌هاوس با چشم‌انداز ۳۶۰", "penthouse", "الهیه", 2500000, 8, 4, 3, "wifi,pool,tv,washer", "/images/pent1.jpg"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO properties (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, amenities, images) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        properties
    )

    messages = [
        ("ناشناس", "test@mail.com", "09120000000", "feedback", "عالی هستید", 0),
        ("زهرا", "zahra@mail.com", "09135556677", "booking", "مشکل در رزرو", 0),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO messages (fullname, email, phone, topic, message_text, is_read) VALUES (?,?,?,?,?,?)",
        messages
    )

    cart_items = [(2, 1), (2, 3)]
    cursor.executemany("INSERT OR IGNORE INTO cart (user_id, property_id) VALUES (?,?)", cart_items)

    wishlist_items = [(2, 4), (2, 2)]
    cursor.executemany("INSERT OR IGNORE INTO wishlist (user_id, property_id) VALUES (?,?)", wishlist_items)

    comments = [
        (2, 1, "اقامتگاه فوق‌العاده‌ای بود!", 5),
        (4, 1, "محیط آرام و تمیز", 4),
        (2, 2, "موقعیت مکانی عالی", 5),
    ]
    cursor.executemany("INSERT OR IGNORE INTO comments (user_id, property_id, comment_text, rating) VALUES (?,?,?,?)", comments)

    conn.commit()
    conn.close()
    print("✅ داده‌های آزمایشی با موفقیت اضافه شدند.")

if __name__ == "__main__":
    seed()