
import sqlite3
import os

DB_NAME = "accommodation.db"

def create_connection(db_file):
    """ایجاد اتصال به دیتابیس SQLite"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"اتصال به '{db_file}' با موفقیت برقرار شد.")
    except sqlite3.Error as e:
        print(f"خطا در اتصال: {e}")
    return conn

def create_tables(conn):
    """ساخت جداول مورد نیاز در صورت عدم وجود"""
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
        main_image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """

    create_amenities_table = """
    CREATE TABLE IF NOT EXISTS amenities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """

    create_property_amenities_table = """
    CREATE TABLE IF NOT EXISTS property_amenities (
        property_id INTEGER NOT NULL,
        amenity_id INTEGER NOT NULL,
        PRIMARY KEY (property_id, amenity_id),
        FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
        FOREIGN KEY (amenity_id) REFERENCES amenities(id) ON DELETE CASCADE
    );
    """

    create_property_images_table = """
    CREATE TABLE IF NOT EXISTS property_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER NOT NULL,
        image_url TEXT NOT NULL,
        is_main INTEGER DEFAULT 0,
        FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
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

    tables = [
        create_users_table,
        create_properties_table,
        create_amenities_table,
        create_property_amenities_table,
        create_property_images_table,
        create_messages_table
    ]

    try:
        cursor = conn.cursor()
        for table_sql in tables:
            cursor.execute(table_sql)
        conn.commit()
        print("تمام جداول با موفقیت ایجاد / به‌روز شدند.")
    except sqlite3.Error as e:
        print(f"خطا در ساخت جداول: {e}")

def insert_initial_amenities(conn):
    """درج امکانات اولیه (در صورت خالی بودن جدول)"""
    amenities_list = [
        ('wifi',), ('parking',), ('pool',), ('kitchen',),
        ('air_conditioning',), ('tv',), ('washer',), ('pet_friendly',)
    ]
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM amenities")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany("INSERT INTO amenities (name) VALUES (?)", amenities_list)
            conn.commit()
            print("امکانات پیش‌فرض اضافه شدند.")
        else:
            print("جدول امکانات خالی نیست، درج نشد.")
    except sqlite3.Error as e:
        print(f"خطا در درج امکانات: {e}")

def main():
    if os.path.exists(DB_NAME):
        print(f"دیتابیس '{DB_NAME}' از قبل موجود است.")
    else:
        print(f"دیتابیس '{DB_NAME}' وجود ندارد. یک دیتابیس جدید ساخته می‌شود.")

    conn = create_connection(DB_NAME)
    if conn is not None:
        create_tables(conn)
        insert_initial_amenities(conn)
        conn.close()
        print("عملیات به پایان رسید.")
    else:
        print("اتصال به دیتابیس انجام نشد.")

if __name__ == "__main__":
    main()
