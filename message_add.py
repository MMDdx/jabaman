
import sqlite3

DB_NAME = "accommodation.db"


def add_message():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    message_data = (
        "مریم احمدی",
        "maryam@example.com",
        "09187654321",
        "feedback",
        "پلتفرم عالی‌ای دارید، پیشنهاد می‌کنم فیلتر جستجو را بهبود دهید."
    )

    try:
        cursor.execute(
            "INSERT INTO messages (fullname, email, phone, topic, message_text) VALUES (?, ?, ?, ?, ?)",
            message_data
        )
        conn.commit()
        print("پیام جدید با موفقیت ثبت شد.")
    except sqlite3.Error as e:
        print(f"خطا در افزودن پیام: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    add_message()