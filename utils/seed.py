# seed.py
import sqlite3
from hashlib import sha256

DB_NAME = "db.sqlite"

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def seed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ---------- کاربران ----------
    users = [
        ("علی", "محمدی", "09123456789", hash_password("12345678"), "host"),
        ("مریم", "احمدی", "09187654321", hash_password("87654321"), "guest"),
        ("رضا", "کریمی", "09351234567", hash_password("password"), "host"),
        ("سارا", "نیکپور", "09121112222", hash_password("sara1234"), "guest"),
    ]
    try:
        cursor.executemany(
            "INSERT OR IGNORE INTO users (first_name, last_name, phone, password, account_type) VALUES (?,?,?,?,?)",
            users
        )
    except Exception as e:
        print(f"خطا در درج کاربران: {e}")

    # ---------- اقامتگاه‌ها ----------
    properties = [
        (
            1, "ویلای ساحلی رویایی", "ویلایی زیبا با منظره دریا و امکانات کامل", "villa",
            "مازندران، محمودآباد", 1200000, 6, 3, 2,
            "wifi,parking,pool,kitchen", "/static/images/villa1.jpg,/static/images/villa1_2.jpg"
        ),
        (
            3, "آپارتمان مدرن شهری", "آپارتمانی شیک در مرکز شهر", "apartment",
            "تهران، خیابان انقلاب", 850000, 4, 2, 1,
            "wifi,tv,air_conditioning", "/static/images/apart1.jpg"
        ),
        (
            1, "کلبه جنگلی دنج", "کلبه‌ای چوبی در دل جنگل", "cottage",
            "مازندران، نور", 650000, 4, 2, 1,
            "parking,kitchen,pet_friendly", "/static/images/cottage1.jpg,/static/images/cottage1_2.jpg"
        ),
        (
            3, "پنت‌هاوس لوکس", "پنت‌هاوسی با چشم‌انداز ۳۶۰ درجه", "penthouse",
            "تهران، الهیه", 2500000, 8, 4, 3,
            "wifi,parking,pool,tv,air_conditioning,washer", "/static/images/pent1.jpg"
        ),
    ]
    try:
        cursor.executemany(
            """INSERT OR IGNORE INTO properties 
               (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, amenities, images)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            properties
        )
    except Exception as e:
        print(f"خطا در درج اقامتگاه‌ها: {e}")

    # ---------- پیام‌ها ----------
    messages = [
        ("کاربر ناشناس", "test@mail.com", "09120000000", "feedback", "پلتفرم عالی‌ای دارید!", 0),
        ("زهرا حسینی", "zahra@example.com", "09135556677", "booking-issue", "مشکل در پرداخت داشتم.", 0),
        ("مهمان", "", "", "host-assistance", "چگونه اقامتگاه ثبت کنم؟", 1),
    ]
    try:
        cursor.executemany(
            "INSERT OR IGNORE INTO messages (fullname, email, phone, topic, message_text, is_read) VALUES (?,?,?,?,?,?)",
            messages
        )
    except Exception as e:
        print(f"خطا در درج پیام‌ها: {e}")

    conn.commit()
    conn.close()
    print("داده‌های آزمایشی با موفقیت اضافه شدند.")

if __name__ == "__main__":
    seed()