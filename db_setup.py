# db_setup.py
import sqlite3
import os

DB_NAME = "db.sqlite"

EXPECTED_SCHEMA = {
    "users": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "first_name": "TEXT NOT NULL",
        "last_name": "TEXT NOT NULL",
        "phone": "TEXT UNIQUE NOT NULL",
        "password": "TEXT NOT NULL",
        "account_type": "TEXT NOT NULL CHECK(account_type IN ('guest', 'host'))",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    },
    "properties": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "host_id": "INTEGER NOT NULL",
        "title": "TEXT NOT NULL",
        "description": "TEXT",
        "property_type": "TEXT NOT NULL CHECK(property_type IN ('villa', 'apartment', 'cottage', 'villa-garden', 'penthouse', 'other'))",
        "location": "TEXT NOT NULL",
        "price_per_night": "REAL NOT NULL",
        "max_guests": "INTEGER NOT NULL",
        "bedrooms": "INTEGER DEFAULT 0",
        "bathrooms": "INTEGER DEFAULT 0",
        "amenities": "TEXT",
        "images": "TEXT",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    },
    "messages": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "fullname": "TEXT NOT NULL",
        "email": "TEXT",
        "phone": "TEXT",
        "topic": "TEXT",
        "message_text": "TEXT NOT NULL",
        "is_read": "INTEGER DEFAULT 0",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
}

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"اتصال به '{db_file}' با موفقیت برقرار شد.")
    except sqlite3.Error as e:
        print(f"خطا در اتصال: {e}")
    return conn

def get_existing_columns(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return {row[1]: row[2] for row in rows}

def create_tables(conn):
    """ایجاد جداول در صورت عدم وجود (با ساختار اولیه کامل)"""
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        account_type TEXT NOT NULL CHECK(account_type IN ('guest', 'host')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_properties_table = """
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        property_type TEXT NOT NULL CHECK(property_type IN ('villa', 'apartment', 'cottage', 'villa-garden', 'penthouse', 'other')),
        location TEXT NOT NULL,
        price_per_night REAL NOT NULL,
        max_guests INTEGER NOT NULL,
        bedrooms INTEGER DEFAULT 0,
        bathrooms INTEGER DEFAULT 0,
        amenities TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    create_messages_table = """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        topic TEXT,
        message_text TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    tables = [create_users_table, create_properties_table, create_messages_table]
    try:
        cursor = conn.cursor()
        for table_sql in tables:
            cursor.execute(table_sql)
        conn.commit()
        print("جداول اصلی (در صورت عدم وجود) ساخته شدند.")
    except sqlite3.Error as e:
        print(f"خطا در ساخت جداول: {e}")

def migrate_table(conn, table_name, expected_columns):
    """اضافه کردن ستون‌های جدید و حذف ستون‌های اضافی (با بازسازی)"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        return  # جدول نیست -> create_tables می‌سازد

    existing = get_existing_columns(conn, table_name)
    expected_set = set(expected_columns.keys())
    existing_set = set(existing.keys())

    # ستون‌های جدید (در expected هست، در existing نیست)
    new_columns = expected_set - existing_set
    # ستون‌های اضافی (در existing هست، در expected نیست)
    extra_columns = existing_set - expected_set

    # 1. اضافه کردن ستون‌های جدید با ALTER TABLE
    for col in new_columns:
        col_type = expected_columns[col]
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}")
            print(f"ستون '{col}' به جدول '{table_name}' اضافه شد.")
        except sqlite3.Error as e:
            print(f"خطا در افزودن ستون '{col}': {e}")

    # 2. حذف ستون‌های اضافی (در صورت وجود)
    if extra_columns:
        print(f"ستون‌های اضافی در جدول '{table_name}': {extra_columns}")
        # برای حذف، باید جدول را بازسازی کنیم
        # مراحل: ایجاد جدول موقت، کپی داده‌ها، حذف جدول اصلی، تغییر نام
        # ابتدا لیست ستون‌های مجاز (مورد انتظار) را به ترتیب درست از expected بگیریم
        # اما باید ستون‌هایی که از قبل وجود دارند و در expected هم هستند حفظ شوند
        common_columns = expected_set & existing_set  # ستون‌هایی که باید نگه داشته شوند

        # ساخت یک جدول جدید با ساختار کامل
        columns_def = ", ".join([f"{col} {expected_columns[col]}" for col in expected_columns])
        temp_table = f"{table_name}_temp"
        cursor.execute(f"CREATE TABLE {temp_table} ({columns_def})")

        # کپی داده‌ها از جدول اصلی به جدول موقت فقط برای ستون‌های common
        cols_list = ", ".join(common_columns)
        cursor.execute(f"INSERT INTO {temp_table} ({cols_list}) SELECT {cols_list} FROM {table_name}")

        # حذف جدول اصلی
        cursor.execute(f"DROP TABLE {table_name}")

        # تغییر نام جدول موقت به اصلی
        cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")

        conn.commit()
        print(f"ستون‌های اضافی '{extra_columns}' از جدول '{table_name}' حذف شدند.")
    else:
        if not new_columns:
            print(f"جدول '{table_name}' کاملاً مطابق است.")

def migrate_if_needed(conn):
    """بررسی و هماهنگ‌سازی تمام جداول"""
    for table_name, columns in EXPECTED_SCHEMA.items():
        migrate_table(conn, table_name, columns)

def main():
    if os.path.exists(DB_NAME):
        print(f"دیتابیس '{DB_NAME}' از قبل موجود است.")
    else:
        print(f"دیتابیس '{DB_NAME}' وجود ندارد. یک دیتابیس جدید ساخته می‌شود.")

    conn = create_connection(DB_NAME)
    if conn is not None:
        create_tables(conn)          # جداول را در صورت عدم وجود بساز
        migrate_if_needed(conn)      # ستون‌های جدید را اضافه و ستون‌های اضافی را حذف کن
        conn.close()
        print("عملیات به پایان رسید.")
    else:
        print("اتصال به دیتابیس انجام نشد.")

if __name__ == "__main__":
    main()