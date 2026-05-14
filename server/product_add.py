
import sqlite3

DB_NAME = "accommodation.db"


def add_property():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    property_data = (
        1,  # host_id
        "ویلای دنج جنگلی",
        "ویلایی زیبا با منظره جنگل، امکانات کامل، مناسب ۴ نفر",
        "villa",
        "مازندران، نور، جنگل واز",
        850000,  # قیمت هر شب به تومان
        4,  # حداکثر مهمان
        2,  # اتاق خواب
        1  # سرویس بهداشتی
    )

    try:
        cursor.execute(
            """INSERT INTO properties
               (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            property_data
        )
        conn.commit()
        print("اقامتگاه جدید با موفقیت ثبت شد.")
    except sqlite3.IntegrityError as e:
        print(f"خطا در افزودن اقامتگاه: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    add_property()