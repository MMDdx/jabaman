# models/_shared.py
"""زیرساخت مشترک لایه‌ی Model — اتصال به دیتابیس و helperهای پایه.

این ماژول هیچ‌گونه منطق دامنه‌ای ندارد؛ فقط ابزارهای پایه‌ای فراهم می‌کند که
بقیه‌ی ماژول‌های domain از آن‌ها استفاده می‌کنند:

- DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT: پیش‌فرض هزینه‌ی مهمان اضافی.
- EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT: نام قدیمی برای backward-compat.
- DB_NAME: نام فایل دیتابیس (همان که در db_setup تعریف شده).
- get_db(): باز کردن یک اتصال جدید با FK و Row factory.
- _dict(): تبدیل sqlite3.Row به dict (یا None).
"""
import sqlite3

import db_setup


# هزینه‌ی پیش‌فرض هر مهمان اضافی در هر شب (تومان)
# این مقدار فقط برای اقامتگاه‌های جدید به‌عنوان پیش‌فرض استفاده می‌شود.
# هر میزبان می‌تواند با فیلد properties.extra_guest_charge این مقدار را
# برای اقامتگاه خودش به‌صورت مجزا تنظیم کند.
DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT = 100_000

# برای backward-compatibility: نام قدیمی ثابت همچنان به مقدار پیش‌فرض اشاره می‌کند.
EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT = DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT

# استفاده از همان نام دیتابیس که در db_setup تعریف شده
DB_NAME = db_setup.DB_NAME


def get_db():
    """باز کردن یک اتصال جدید به دیتابیس با فعال بودن FK و Row factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _dict(row):
    """تبدیل sqlite3.Row به dict. اگر None باشد، None برمی‌گرداند."""
    return dict(row) if row is not None else None
