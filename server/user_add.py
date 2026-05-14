
import sqlite3

DB_NAME = "accommodation.db"


def add_user():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    user_data = (
        "علی",
        "محمدی",
        "09123456789",
        "hashed_password_placeholder",
        "host"
    )

    try:
        cursor.execute(
            "INSERT INTO users (first_name, last_name, phone, password_hash, account_type) VALUES (?, ?, ?, ?, ?)",
            user_data
        )
        conn.commit()
        print("کاربر جدید با موفقیت اضافه شد.")
    except sqlite3.IntegrityError as e:
        print(f"خطا در افزودن کاربر: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    add_user()