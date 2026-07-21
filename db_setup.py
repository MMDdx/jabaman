# db_setup.py
"""ساخت و مهاجرت دیتابیس SQLite برای پلتفرم اجاره اقامتگاه.

تغییرات نسبت به نسخه‌ی قبل:
- فیلد `email` جایگزین `phone` به‌عنوان شناسه یکتای ورود شده است.
- `phone` همچنان به‌عنوان فیلد اختیاری برای تماس باقی مانده است.
- `is_admin` به جدول users اضافه شده تا کنترل دسترسی مسیرهای /admin ممکن شود.
- `is_admin` به‌صورت BOOLEAN تعریف می‌شود (در SQLite هم‌معنی INTEGER 0/1 است،
  اما از نظر خوانایی کد و قصد برنامه‌نویس، Boolean است).
- PRAGMA foreign_keys = ON فعال شده تا ON DELETE CASCADE واقعاً کار کند.
"""
import sqlite3
import os

# مسیر مطلق دیتابیس (نسبت به ریشه‌ی پروژه)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "db.sqlite")

EXPECTED_SCHEMA = {
    "users": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "first_name": "TEXT NOT NULL",
        "last_name": "TEXT NOT NULL",
        "email": "TEXT UNIQUE NOT NULL",
        "phone": "TEXT",
        "password": "TEXT NOT NULL",
        "account_type": "TEXT NOT NULL CHECK(account_type IN ('guest', 'host'))",
        "is_admin": "BOOLEAN DEFAULT 0",
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
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY (host_id)": "REFERENCES users(id) ON DELETE CASCADE"
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
    },
    "cart": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "property_id": "INTEGER NOT NULL",
        "added_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY (user_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY (property_id)": "REFERENCES properties(id) ON DELETE CASCADE"
    },
    "wishlist": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "property_id": "INTEGER NOT NULL",
        "added_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY (user_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY (property_id)": "REFERENCES properties(id) ON DELETE CASCADE"
    },
    "comments": {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "property_id": "INTEGER NOT NULL",
        "comment_text": "TEXT NOT NULL",
        "rating": "INTEGER DEFAULT 5",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY (user_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY (property_id)": "REFERENCES properties(id) ON DELETE CASCADE"
    },
    "sessions": {
        "id": "TEXT PRIMARY KEY",
        "user_id": "INTEGER NOT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "expires_at": "TIMESTAMP",
        "FOREIGN KEY (user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    }
}


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON")
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
    tables_sql = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            account_type TEXT NOT NULL CHECK(account_type IN ('guest', 'host')),
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS properties (
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
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            topic TEXT,
            message_text TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_id INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )"""
    ]
    try:
        cursor = conn.cursor()
        for sql in tables_sql:
            cursor.execute(sql)
        conn.commit()
        print("تمامی جداول (در صورت عدم وجود) ساخته شدند.")
    except sqlite3.Error as e:
        print(f"خطا در ساخت جداول: {e}")


def _needs_rebuild(expected_columns, new_columns, existing):
    """بررسی اینکه آیا نیاز به بازسازی جدول است.

    SQLite نمی‌تواند ستون‌های UNIQUE یا NOT NULL بدون DEFAULT را با ALTER TABLE اضافه کند.
    در این موارد باید جدول را بازسازی کنیم.
    همچنین اگر نوع ستون موجود تغییر کرده باشد (مثلاً phone از UNIQUE به غیر UNIQUE).
    """
    reasons = []

    for col in new_columns:
        if col.startswith("FOREIGN KEY"):
            continue
        col_type = expected_columns[col].upper()
        if "UNIQUE" in col_type:
            reasons.append(f"ستون جدید '{col}' دارای UNIQUE است")
        elif "NOT NULL" in col_type and "DEFAULT" not in col_type:
            reasons.append(f"ستون جدید '{col}' دارای NOT NULL بدون DEFAULT است")

    return reasons


def _get_existing_unique_columns(conn, table_name):
    """گرفتن لیست ستون‌هایی که UNIQUE هستند در جدول فعلی.

    نکته: INTEGER PRIMARY KEY در SQLite به‌صورت ضمنی UNIQUE است اما
    ایندکس خودکار نمی‌سازد، پس باید آن را به‌صورت جداگانه بررسی کنیم.
    """
    cursor = conn.cursor()
    unique_cols = set()

    # روش ۱: بررسی ایندکس‌های UNIQUE
    cursor.execute(f"PRAGMA index_list({table_name})")
    for row in cursor.fetchall():
        # row: [seq, name, unique, origin, partial]
        if row[2]:  # unique = 1
            cursor.execute(f"PRAGMA index_info({row[1]})")
            for col_info in cursor.fetchall():
                unique_cols.add(col_info[2])  # column name

    # روش ۲: بررسی ستون‌های PRIMARY KEY (implicit unique)
    cursor.execute(f"PRAGMA table_info({table_name})")
    for col in cursor.fetchall():
        # col: [cid, name, type, notnull, dflt_value, pk]
        if col[5] == 1:  # pk = 1 (هر ستون PRIMARY KEY)
            unique_cols.add(col[1])

    return unique_cols


def rebuild_table(conn, table_name, expected_columns, existing_columns):
    """بازسازی جدول با اسکیمای جدید، حفظ داده‌های قدیمی هرجا که ممکن باشد.

    این تابع برای موارد زیر استفاده می‌شود:
    - اضافه‌کردن ستون UNIQUE جدید
    - اضافه‌کردن ستون NOT NULL بدون DEFAULT
    - تغییر نوع ستون موجود (مثلاً تغییر UNIQUE به غیر UNIQUE)
    - حذف ستون اضافی

    نکته مهم: FK را موقتاً غیرفعال می‌کنیم چون در غیر این صورت
    DROP TABLE باعث CASCADE DELETE در جداول وابسته می‌شود.
    """
    cursor = conn.cursor()

    # غیرفعال‌کردن FK برای جلوگیری از CASCADE DELETE هنگام DROP TABLE
    cursor.execute("PRAGMA foreign_keys = OFF")

    try:
        # ساخت تعریف ستون‌های جدید (بدون FK ها)
        col_defs = []
        expected_data_cols = []
        for col, col_type in expected_columns.items():
            if col.startswith("FOREIGN KEY"):
                continue
            col_defs.append(f"{col} {col_type}")
            expected_data_cols.append(col)

        columns_def_str = ", ".join(col_defs)

        # اضافه‌کردن تعاریف FOREIGN KEY
        fk_defs = []
        for col, col_type in expected_columns.items():
            if col.startswith("FOREIGN KEY"):
                fk_defs.append(f"{col} {col_type}")

        if fk_defs:
            columns_def_str += ", " + ", ".join(fk_defs)

        # ساخت جدول موقت
        temp_table = f"{table_name}_temp"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(f"CREATE TABLE {temp_table} ({columns_def_str})")

        # ستون‌های مشترک (هم در قدیم هم در جدید)
        common = [c for c in expected_data_cols if c in existing_columns]
        # ستون‌های جدید
        new_cols = [c for c in expected_data_cols if c not in existing_columns]

        if common or new_cols:
            insert_cols = list(common)
            select_cols = list(common)

            # برای ستون‌های جدید، مقدار مناسب انتخاب کن
            for new_col in new_cols:
                col_type = expected_columns[new_col].upper()

                # مورد خاص: ستون email که از phone قدیمی پر می‌شود
                if new_col == "email" and "phone" in existing_columns:
                    # phone قدیمی را به email تبدیل می‌کنیم (با افزودن @example.com)
                    # چون phone قبلاً UNIQUE بوده، email هم UNIQUE خواهد بود
                    insert_cols.append("email")
                    select_cols.append("phone || '@example.com'")

                # مورد خاص: ستون is_admin که پیش‌فرض 0 می‌گیرد
                elif new_col == "is_admin":
                    insert_cols.append("is_admin")
                    select_cols.append("0")

                # ستون‌های NOT NULL عددی
                elif "NOT NULL" in col_type and ("INTEGER" in col_type or "REAL" in col_type):
                    insert_cols.append(new_col)
                    select_cols.append("0" if "INTEGER" in col_type else "0.0")

                # ستون‌های NOT NULL متنی
                elif "NOT NULL" in col_type:
                    insert_cols.append(new_col)
                    select_cols.append("''")

                # ستون‌های nullable → چیزی اضافه نمی‌کنیم (NULL می‌شوند)
                else:
                    pass

            if insert_cols:
                insert_str = ", ".join(insert_cols)
                select_str = ", ".join(select_cols)
                cursor.execute(
                    f"INSERT INTO {temp_table} ({insert_str}) "
                    f"SELECT {select_str} FROM {table_name}"
                )

        # جابجایی جدول‌ها
        cursor.execute(f"DROP TABLE {table_name}")
        cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
        conn.commit()
        print(f"✓ جدول '{table_name}' با موفقیت بازسازی شد.")
    finally:
        # فعال‌کردن مجدد FK
        cursor.execute("PRAGMA foreign_keys = ON")


def migrate_table(conn, table_name, expected_columns):
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        return

    existing = get_existing_columns(conn, table_name)
    expected_set = set(expected_columns.keys())
    existing_set = set(existing.keys())

    new_columns = expected_set - existing_set
    extra_columns = existing_set - expected_set

    # ---------- بررسی نیاز به بازسازی جدول ----------
    rebuild_reasons = _needs_rebuild(expected_columns, new_columns, existing)

    # بررسی تغییر UNIQUE بودن ستون‌های موجود
    existing_unique_cols = _get_existing_unique_columns(conn, table_name)
    for col in (expected_set & existing_set):
        if col.startswith("FOREIGN KEY"):
            continue
        expected_type = expected_columns[col].upper()
        was_unique = col in existing_unique_cols
        # PRIMARY KEY هم به‌عنوان UNIQUE در نظر گرفته می‌شود
        will_be_unique = "UNIQUE" in expected_type or "PRIMARY KEY" in expected_type
        if was_unique and not will_be_unique:
            rebuild_reasons.append(f"ستون '{col}' از UNIQUE به غیر UNIQUE تغییر یافته")
        elif not was_unique and will_be_unique:
            rebuild_reasons.append(f"ستون '{col}' از غیر UNIQUE به UNIQUE تغییر یافته")

    # اگر نیاز به بازسازی بود یا ستون اضافی داشتیم
    if rebuild_reasons or extra_columns:
        if rebuild_reasons:
            print(f"\n⚠️  بازسازی جدول '{table_name}' به دلایل:")
            for r in rebuild_reasons:
                print(f"   - {r}")
        if extra_columns:
            print(f"   - ستون‌های اضافی برای حذف: {extra_columns}")
        rebuild_table(conn, table_name, expected_columns, existing)
        return

    # ---------- افزودن ساده ستون‌های جدید (بدون UNIQUE یا NOT NULL بدون DEFAULT) ----------
    for col in new_columns:
        col_type = expected_columns[col]
        if col.startswith("FOREIGN KEY"):
            continue
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}")
            print(f"✓ ستون '{col}' به جدول '{table_name}' اضافه شد.")
        except sqlite3.Error as e:
            print(f"خطا در افزودن ستون '{col}': {e}")


def migrate_if_needed(conn):
    for table_name, columns in EXPECTED_SCHEMA.items():
        migrate_table(conn, table_name, columns)


def main():
    if os.path.exists(DB_NAME):
        print(f"دیتابیس '{DB_NAME}' از قبل موجود است.")
    else:
        print(f"دیتابیس '{DB_NAME}' وجود ندارد. یک دیتابیس جدید ساخته می‌شود.")

    conn = create_connection(DB_NAME)
    if conn is not None:
        create_tables(conn)
        migrate_if_needed(conn)
        conn.close()
        print("عملیات به پایان رسید.")
    else:
        print("اتصال به دیتابیس انجام نشد.")


if __name__ == "__main__":
    main()
