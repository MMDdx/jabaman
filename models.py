# models.py
"""لایه‌ی Model در معماری MVC — تمام دسترسی‌های دیتابیس اینجا انجام می‌شود.

تغییرات نسبت به نسخه‌ی قبل:
- PRAGMA foreign_keys = ON در get_db فعال شده تا CASCADE واقعاً کار کند.
- کاربران با email لاگین می‌کنند (نه phone).
- پارامترهای password به password_hash تغییر نام داد (شفاف‌تر).
- توابع delete_from_cart و delete_from_wishlist اضافه شد.
- توابع get_user_by_email، get_user_with_role اضافه شد.
- توابع create_session و get_user_by_session با مدیریت انقضا.
- استفاده از context manager برای جلوگیری از connection leak.
- is_admin به‌صورت Boolean (در ساخت کاربر) استفاده می‌شود.
- توابع get_user_account_type و is_host برای کنترل دسترسی میزبان/مهمان.
- توابع مدیریت رزرو: add_to_cart با تاریخ و تعداد مهمان، محاسبه قیمت با
  هزینه‌ی مهمان اضافی، بررسی هم‌پوشانی تاریخ رزرو، ایجاد رزرو، لغو رزرو.
- ثابت DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT به‌عنوان پیش‌فرض
  برای اقامتگاه‌های جدید. هر میزبان می‌تواند این مقدار را برای اقامتگاه
  خودش با فیلد properties.extra_guest_charge تغییر دهد.
- توابع get_all_reservations و cancel_reservation_as_admin برای پنل ادمین.
- تولید reservation_code تصادفی یکتا (JAB-XXXXXX) هنگام ایجاد رزرو و
  ذخیره‌ی آن در دیتابیس — این شناسه به‌جای شماره‌ی متوالی به کاربر نشان داده می‌شود.
"""
import sqlite3
import uuid
import secrets
import string
from datetime import datetime, timedelta, date

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


# ===================== کاربران =====================

def get_user(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _dict(row)


def get_all_users():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, first_name, last_name, email, phone, account_type, is_admin, created_at "
            "FROM users ORDER BY id ASC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_user_by_email(email):
    """برای ورود با ایمیل."""
    if not email:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _dict(row)


def create_user(first_name, last_name, email, password_hash, account_type,
                phone=None, is_admin=False):
    """ساخت کاربر جدید.

    پارامترها:
      is_admin: bool (پیش‌فرض False).
                در DB به‌صورت 0/1 ذخیره می‌شود (SQLite BOOLEAN هم‌معنی INTEGER است).
    """
    # تبدیل bool به 0/1 برای ذخیره در SQLite
    is_admin_val = 1 if is_admin else 0
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, phone, password, account_type, is_admin) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, phone, password_hash, account_type, is_admin_val)
        )
        conn.commit()


def update_user(user_id, first_name, last_name, email, account_type, phone=None):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET first_name=?, last_name=?, email=?, phone=?, account_type=? WHERE id=?",
            (first_name, last_name, email, phone, account_type, user_id)
        )
        conn.commit()


def is_admin(user_id):
    """بررسی اینکه آیا کاربر admin است یا نه. خروجی همیشه bool است."""
    if not user_id:
        return False
    with get_db() as conn:
        row = conn.execute(
            "SELECT is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        return False
    # SQLite ممکن است 0/1 یا True/False برگرداند؛ در هر صورت bool می‌سازیم
    val = row["is_admin"]
    return bool(val) and val != 0


def get_user_account_type(user_id):
    """گرفتن نوع حساب کاربر ('guest' یا 'host').

    اگر کاربر وجود نداشت یا وارد نشده بود، None برمی‌گرداند.
    کاربرد: کنترل دسترسی به دکمه‌ی «افزودن اقامتگاه» در navbar
    که فقط باید برای میزبان‌ها نمایش داده شود.
    """
    if not user_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT account_type FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if not row:
        return None
    return row["account_type"]


def is_host(user_id):
    """بررسی اینکه آیا کاربر میزبان است یا نه. خروجی همیشه bool است."""
    return get_user_account_type(user_id) == 'host'


# ===================== اقامتگاه‌ها =====================

def get_all_properties():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, host_id, title, property_type, location, price_per_night, "
            "max_guests, bedrooms, bathrooms, description, amenities, images, "
            "is_reserved, extra_guest_charge, created_at, updated_at "
            "FROM properties ORDER BY id DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_property(property_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
    return _dict(row)


def get_featured_properties(limit=6):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, property_type, location, price_per_night "
            "FROM properties ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_properties_by_host(host_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM properties WHERE host_id = ? ORDER BY id DESC",
            (host_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def create_property(host_id, title, description, property_type, location,
                    price_per_night, max_guests, bedrooms, bathrooms,
                    amenities=None, images=None,
                    extra_guest_charge=None):
    """ساخت اقامتگاه جدید.

    پارامترها:
      extra_guest_charge: هزینه‌ی هر مهمان اضافی در هر شب (تومان).
        اگر None باشد، از DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT استفاده می‌شود.
    """
    if extra_guest_charge is None:
        extra_guest_charge = DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT
    try:
        egc = float(extra_guest_charge)
    except (TypeError, ValueError):
        egc = float(DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    if egc < 0:
        egc = 0.0
    with get_db() as conn:
        conn.execute(
            "INSERT INTO properties "
            "(host_id, title, description, property_type, location, price_per_night, "
            " max_guests, bedrooms, bathrooms, amenities, images, extra_guest_charge) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (host_id, title, description, property_type, location, price_per_night,
             max_guests, bedrooms, bathrooms, amenities, images, egc)
        )
        conn.commit()


def update_property(property_id, title, description, property_type, location,
                    price_per_night, max_guests, bedrooms, bathrooms,
                    amenities=None, images=None,
                    extra_guest_charge=None):
    """به‌روزرسانی اقامتگاه.

    پارامترها:
      extra_guest_charge: هزینه‌ی هر مهمان اضافی در هر شب (تومان).
        اگر None باشد، مقدار فعلی در DB حفظ می‌شود (تغییر نمی‌کند).
    """
    # گرفتن مقدار فعلی اگر extra_guest_charge پاس نشده
    if extra_guest_charge is None:
        with get_db() as conn:
            row = conn.execute(
                "SELECT extra_guest_charge FROM properties WHERE id = ?",
                (property_id,)
            ).fetchone()
        egc = float(row["extra_guest_charge"]) if row and row["extra_guest_charge"] is not None \
            else float(DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    else:
        try:
            egc = float(extra_guest_charge)
        except (TypeError, ValueError):
            egc = float(DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    if egc < 0:
        egc = 0.0

    with get_db() as conn:
        conn.execute(
            "UPDATE properties SET title=?, description=?, property_type=?, location=?, "
            "price_per_night=?, max_guests=?, bedrooms=?, bathrooms=?, amenities=?, images=?, "
            "extra_guest_charge=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, description, property_type, location, price_per_night,
             max_guests, bedrooms, bathrooms, amenities, images, egc, property_id)
        )
        conn.commit()


def delete_property(property_id):
    with get_db() as conn:
        conn.execute("DELETE FROM properties WHERE id = ?", (property_id,))
        conn.commit()


def delete_user(user_id):
    """حذف کاربر — به‌خاطر ON DELETE CASCADE در جداول وابسته،
    اقامتگاه‌ها، نظرات، سبد و علاقه‌مندی‌های او هم حذف می‌شوند.
    """
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


# ===================== پیام‌ها =====================

def get_all_messages():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, fullname, email, phone, topic, message_text, is_read, created_at "
            "FROM messages ORDER BY id DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_message(message_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return _dict(row)


def create_message(fullname, email, phone, topic, message_text):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (fullname, email, phone, topic, message_text) "
            "VALUES (?, ?, ?, ?, ?)",
            (fullname, email, phone, topic, message_text)
        )
        conn.commit()


def mark_message_read(message_id, is_read=True):
    with get_db() as conn:
        conn.execute(
            "UPDATE messages SET is_read = ? WHERE id = ?",
            (1 if is_read else 0, message_id)
        )
        conn.commit()


def delete_message(message_id):
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        conn.commit()


# ===================== نظرات =====================

def get_comments_for_property(property_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.comment_text, c.rating, c.created_at, "
            "       u.first_name || ' ' || u.last_name AS user_name "
            "FROM comments c JOIN users u ON c.user_id = u.id "
            "WHERE c.property_id = ? ORDER BY c.created_at DESC",
            (property_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_all_comments():
    """گرفتن همه‌ی نظرات (برای پنل ادمین) به‌همراه نام کاربر و عنوان اقامتگاه."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.id, c.user_id, c.property_id, c.comment_text, c.rating, c.created_at, "
            "       u.first_name || ' ' || u.last_name AS user_name, "
            "       p.title AS property_title "
            "FROM comments c "
            "JOIN users u ON c.user_id = u.id "
            "JOIN properties p ON c.property_id = p.id "
            "ORDER BY c.created_at DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def get_comment(comment_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM comments WHERE id = ?", (comment_id,)
        ).fetchone()
    return _dict(row)


def delete_comment(comment_id):
    with get_db() as conn:
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()


def add_comment(user_id, property_id, comment_text, rating):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO comments (user_id, property_id, comment_text, rating) "
            "VALUES (?, ?, ?, ?)",
            (user_id, property_id, comment_text, rating)
        )
        conn.commit()


# ===================== سبد خرید =====================

def get_cart_items(user_id):
    """گرفتن آیتم‌های سبد خرید کاربر به‌همراه اطلاعات اقامتگاه و تاریخ/مهمان.

    برای هر آیتم، تعداد شب‌ها و قیمت کل محاسبه می‌شود.
    همچنین برای هر آیتم، هم‌پوشانی با رزروهای تاییدشده‌ی سایر کاربران بررسی
    می‌شود تا در سبد خرید، آیتم‌هایی که تاریخ تداخل دارند به‌صورت ویژه نمایش داده شوند.
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT c.id AS cart_id, c.property_id, c.check_in_date, c.check_out_date, "
            "       c.guests, c.added_at, "
            "       p.id, p.title, p.location, p.price_per_night, p.max_guests, p.images, "
            "       p.is_reserved, p.extra_guest_charge "
            "FROM cart c JOIN properties p ON c.property_id = p.id "
            "WHERE c.user_id = ? ORDER BY c.added_at DESC",
            (user_id,)
        ).fetchall()

    items = []
    for r in rows:
        d = _dict(r)
        # محاسبه‌ی تعداد شب‌ها و قیمت کل برای این آیتم — با هزینه‌ی مهمان اضافی
        # اختصاصی همان اقامتگاه.
        nights, base_price, extra_guests, extra_charge, total = calculate_reservation_price(
            price_per_night=d.get("price_per_night"),
            max_guests=d.get("max_guests"),
            check_in=d.get("check_in_date"),
            check_out=d.get("check_out_date"),
            guests=d.get("guests") or 1,
            extra_guest_charge=d.get("extra_guest_charge"),
        )
        d["nights"] = nights
        d["base_price"] = base_price
        d["extra_guests"] = extra_guests
        d["extra_guest_charge"] = extra_charge
        d["total_price"] = total
        # بررسی هم‌پوشانی تاریخ این آیتم با رزروهای تاییدشده‌ی سایر کاربران
        overlap_available, overlap_err = is_property_available(
            d.get("property_id"),
            d.get("check_in_date"),
            d.get("check_out_date"),
        )
        d["has_overlap"] = not overlap_available
        d["overlap_message"] = overlap_err
        items.append(d)
    return items


def add_to_cart(user_id, property_id, check_in_date=None, check_out_date=None, guests=1):
    """افزودن اقامتگاه به سبد خرید با تاریخ ورود/خروج و تعداد مهمان.

    از INSERT OR IGNORE استفاده نمی‌شود چون می‌خواهیم کاربر بتواند
    همان اقامتگاه را در تاریخ‌های مختلف به سبد اضافه کند.

    خروجی: (success: bool, error_message: str|None)
      - اگر بازه‌ی درخواستی با رزروهای تاییدشده‌ی سایر کاربران هم‌پوشانی داشته باشد،
        success=False و error_message توضیح می‌دهد کدام تاریخ‌ها تداخل دارند.
      - در غیر این صورت، آیتم به سبد اضافه می‌شود و success=True برمی‌گردد.
    """
    # اگر تاریخ‌ها مشخص شده‌اند، هم‌پوشانی با رزروهای تاییدشده را بررسی کن
    if check_in_date and check_out_date:
        available, err = is_property_available(
            property_id, check_in_date, check_out_date
        )
        if not available:
            return False, err

    with get_db() as conn:
        conn.execute(
            "INSERT INTO cart (user_id, property_id, check_in_date, check_out_date, guests) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, property_id, check_in_date, check_out_date, int(guests or 1))
        )
        conn.commit()
    return True, None


def remove_from_cart(user_id, cart_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM cart WHERE id = ? AND user_id = ?",
            (cart_id, user_id)
        )
        conn.commit()


def clear_cart(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()


# ===================== رزرو (Reservations) =====================

def _parse_date(s):
    """تبدیل رشته‌ی تاریخ YYYY-MM-DD به date. در صورت خطا None برمی‌گرداند."""
    if not s:
        return None
    if isinstance(s, date):
        return s
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def calculate_reservation_price(price_per_night, max_guests, check_in, check_out, guests,
                                extra_guest_charge=None):
    """محاسبه‌ی قیمت نهایی رزرو.

    خروجی: tuple از (nights, base_price, extra_guests, extra_guest_charge, total_price)

    - nights: تعداد شب‌ها بین check_in و check_out (حداقل ۱)
    - base_price: price_per_night * nights
    - extra_guests: max(0, guests - max_guests)
    - extra_guest_charge: extra_guests * egc * nights
        که egc هزینه‌ی هر مهمان اضافی در هر شب است (مختص همان اقامتگاه).
        اگر extra_guest_charge پاس نشود، از DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT
        استفاده می‌شود.
    - total_price: base_price + extra_guest_charge

    اگر تاریخ‌ها نامعتبر باشند، nights=1 در نظر گرفته می‌شود.
    """
    try:
        price = float(price_per_night or 0)
    except (TypeError, ValueError):
        price = 0.0

    try:
        mg = int(max_guests or 1)
    except (TypeError, ValueError):
        mg = 1

    try:
        g = int(guests or 1)
    except (TypeError, ValueError):
        g = 1
    if g < 1:
        g = 1

    # هزینه‌ی مهمان اضافی: اگر پاس نشده، از پیش‌فرض سراسری استفاده کن
    if extra_guest_charge is None:
        egc = float(DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    else:
        try:
            egc = float(extra_guest_charge)
        except (TypeError, ValueError):
            egc = float(DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    if egc < 0:
        egc = 0.0

    d_in = _parse_date(check_in)
    d_out = _parse_date(check_out)
    nights = 1
    if d_in and d_out and d_out > d_in:
        nights = (d_out - d_in).days

    base_price = price * nights
    extra_guests = max(0, g - mg)
    extra_guest_charge_total = extra_guests * egc * nights
    total_price = base_price + extra_guest_charge_total

    return nights, base_price, extra_guests, extra_guest_charge_total, total_price


def is_property_available(property_id, check_in, check_out, exclude_reservation_id=None):
    """بررسی اینکه آیا اقامتگاه در بازه‌ی مشخص شده قابل رزرو است یا خیر.

    منطق:
    - یک اقامتگاه می‌تواند در بازه‌های مختلف به چند کاربر رزرو شود. فقط بازه‌های
      هم‌پوشانی نباید قابل رزرو باشند. بنابراین فیلد properties.is_reserved فقط
      یک علامت سریع برای داشتن حداقل یک رزرو فعال است و تصمیم نهایی بر اساس
      هم‌پوشانی تاریخ‌ها گرفته می‌شود.
    - در جدول reservations، رزروهایی با status='confirmed' را بررسی می‌کنیم که
      بازه‌ی آن‌ها با بازه‌ی درخواستی هم‌پوشانی داشته باشد.

    هم‌پوشانی: A.start < B.end AND B.start < A.end
    """
    d_in = _parse_date(check_in)
    d_out = _parse_date(check_out)
    if not d_in or not d_out or d_out <= d_in:
        return False, "تاریخ ورود و خروج نامعتبر است."

    with get_db() as conn:
        # بررسی رزروهای تاییدشده‌ی هم‌پوشان
        if exclude_reservation_id:
            query = (
                "SELECT id, check_in_date, check_out_date FROM reservations "
                "WHERE property_id = ? AND status = 'confirmed' AND id != ? "
                "AND check_in_date < ? AND check_out_date > ?"
            )
            rows = conn.execute(query, (property_id, exclude_reservation_id,
                                        d_out.isoformat(), d_in.isoformat())).fetchall()
        else:
            query = (
                "SELECT id, check_in_date, check_out_date FROM reservations "
                "WHERE property_id = ? AND status = 'confirmed' "
                "AND check_in_date < ? AND check_out_date > ?"
            )
            rows = conn.execute(query, (property_id,
                                        d_out.isoformat(), d_in.isoformat())).fetchall()

    if rows:
        r = rows[0]
        return False, (
            f"این اقامتگاه از {r['check_in_date']} تا {r['check_out_date']} "
            f"توسط کاربر دیگری رزرو شده است."
        )
    return True, None


def _generate_reservation_code():
    """تولید یک شناسه‌ی رزرو تصادفی یکتا به‌فرمت JAB-XXXXXX.

    XXXXXX شامل ۶ کاراکتر از حروف بزرگ و اعداد است (A-Z0-9).
    تلاش می‌کند تا ۱۰ بار کد یکتا تولید کند. اگر همگی تکراری بودند،
    یک UUID کوتاه به‌عنوان fallback برمی‌گرداند.
    """
    alphabet = string.ascii_uppercase + string.digits
    # حذف کاراکترهای به‌راحت اشتباه‌گرفته‌شده (O, 0, I, 1)
    alphabet = "".join(c for c in alphabet if c not in "O0I1")
    for _ in range(10):
        code = "JAB-" + "".join(secrets.choice(alphabet) for _ in range(6))
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM reservations WHERE reservation_code = ?",
                (code,)
            ).fetchone()
        if not row:
            return code
    # fallback بسیار بعید
    return "JAB-" + secrets.token_hex(4).upper()


def create_reservation(user_id, property_id, check_in_date, check_out_date, guests):
    """ایجاد رزرو نهایی برای یک اقامتگاه.

    مراحل:
    1. بررسی در دسترس بودن اقامتگاه در بازه‌ی مشخص شده.
    2. گرفتن اطلاعات اقامتگاه از DB.
    3. محاسبه‌ی قیمت نهایی (با هزینه‌ی مهمان اضافی اختصاصی همان اقامتگاه).
    4. تولید reservation_code تصادفی یکتا.
    5. درج در جدول reservations.
    6. تنظیم is_reserved=1 برای اقامتگاه.

    خروجی: (reservation_id, error_message)
    اگر خطا باشد، reservation_id=None و error_message تنظیم می‌شود.
    در غیر این صورت reservation_id یک dict شامل id و reservation_code است.
    """
    # اعتبارسنجی ورودی
    try:
        guests_int = int(guests)
        if guests_int < 1:
            return None, "تعداد مهمان باید حداقل ۱ باشد."
    except (TypeError, ValueError):
        return None, "تعداد مهمان نامعتبر است."

    # بررسی در دسترس بودن
    available, err = is_property_available(property_id, check_in_date, check_out_date)
    if not available:
        return None, err

    # گرفتن اطلاعات اقامتگاه
    prop = get_property(property_id)
    if not prop:
        return None, "اقامتگاه یافت نشد."

    if guests_int > int(prop.get("max_guests") or 1) * 3:
        # محدودیت امنیتی: حداکثر ۳ برابر ظرفیت مجاز است
        return None, (
            f"تعداد مهمان‌ها بیش از حد مجاز است. حداکثر ظرفیت: "
            f"{prop.get('max_guests')} نفر (با هزینه‌ی اضافی تا ۳ برابر)."
        )

    # محاسبه‌ی قیمت — با هزینه‌ی مهمان اضافی اختصاصی اقامتگاه
    nights, base_price, extra_guests, extra_charge, total = calculate_reservation_price(
        price_per_night=prop.get("price_per_night"),
        max_guests=prop.get("max_guests"),
        check_in=check_in_date,
        check_out=check_out_date,
        guests=guests_int,
        extra_guest_charge=prop.get("extra_guest_charge"),
    )

    # تولید کد رزرو تصادفی یکتا
    reservation_code = _generate_reservation_code()

    # درج در جدول reservations
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO reservations "
            "(reservation_code, user_id, property_id, check_in_date, check_out_date, guests, "
            " extra_guests, extra_guest_charge, nights, base_price, total_price, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed')",
            (reservation_code, user_id, property_id, check_in_date, check_out_date,
             guests_int, extra_guests, extra_charge, nights, base_price, total)
        )
        reservation_id = cur.lastrowid
        # علامت‌گذاری اقامتگاه به‌عنوان رزروشده
        conn.execute(
            "UPDATE properties SET is_reserved = 1, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ?",
            (property_id,)
        )
        conn.commit()

    return {"id": reservation_id, "reservation_code": reservation_code}, None


def get_reservation(reservation_id):
    """گرفتن یک رزرو با id — به‌همراه عنوان و موقعیت اقامتگاه."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT r.*, p.title AS property_title, p.location AS property_location, "
            "       p.price_per_night AS property_price, p.max_guests AS property_max_guests "
            "FROM reservations r "
            "JOIN properties p ON r.property_id = p.id "
            "WHERE r.id = ?",
            (reservation_id,)
        ).fetchone()
    return _dict(row)


def get_user_reservations(user_id):
    """گرفتن همه‌ی رزروهای کاربر — به‌همراه اطلاعات اقامتگاه."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT r.*, p.title AS property_title, p.location AS property_location, "
            "       p.images AS property_images "
            "FROM reservations r "
            "JOIN properties p ON r.property_id = p.id "
            "WHERE r.user_id = ? "
            "ORDER BY r.created_at DESC",
            (user_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_reservations_for_property(property_id):
    """گرفتن رزروهای تاییدشده‌ی یک اقامتگاه (برای نمایش در صفحه‌ی جزئیات)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, reservation_code, check_in_date, check_out_date, status "
            "FROM reservations "
            "WHERE property_id = ? AND status = 'confirmed' "
            "ORDER BY check_in_date ASC",
            (property_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_all_reservations():
    """گرفتن همه‌ی رزروها (برای پنل ادمین) — به‌همراه نام کاربر و عنوان اقامتگاه.

    شامل همه‌ی وضعیت‌ها (confirmed / cancelled / completed) می‌شود.
    به‌ترتیب جدیدترین اول.
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT r.id, r.reservation_code, r.user_id, r.property_id, "
            "       r.check_in_date, r.check_out_date, r.guests, r.extra_guests, "
            "       r.extra_guest_charge, r.nights, r.base_price, r.total_price, "
            "       r.status, r.created_at, "
            "       u.first_name || ' ' || u.last_name AS user_name, "
            "       u.email AS user_email, "
            "       p.title AS property_title, p.location AS property_location "
            "FROM reservations r "
            "JOIN users u ON r.user_id = u.id "
            "JOIN properties p ON r.property_id = p.id "
            "ORDER BY r.created_at DESC"
        ).fetchall()
    return [_dict(r) for r in rows]


def cancel_reservation(reservation_id, user_id=None, is_admin=False):
    """لغو یک رزرو.

    - اگر is_admin=True باشد، user_id نادیده گرفته می‌شود و ادمین می‌تواند
      رزروی هر کاربری را لغو کند.
    - در غیر این صورت، اگر user_id داده شود، فقط رزروی که متعلق به همان کاربر
      است لغو می‌شود.
    - status به 'cancelled' تغییر می‌کند.
    - اگر هیچ رزروی تاییدشده‌ی دیگری برای آن اقامتگاه نباشد، is_reserved به 0 برمی‌گردد.
    """
    with get_db() as conn:
        # بررسی مالکیت رزرو
        if is_admin:
            # ادمین می‌تواند هر رزروی را لغو کند
            row = conn.execute(
                "SELECT property_id, status FROM reservations WHERE id = ?",
                (reservation_id,)
            ).fetchone()
            if not row:
                return False, "رزرو یافت نشد."
            property_id = row["property_id"]
            if row["status"] == "cancelled":
                return False, "این رزرو قبلاً لغو شده است."
        elif user_id is not None:
            row = conn.execute(
                "SELECT user_id, property_id, status FROM reservations WHERE id = ?",
                (reservation_id,)
            ).fetchone()
            if not row:
                return False, "رزرو یافت نشد."
            if row["user_id"] != user_id:
                return False, "شما مجوز لغو این رزرو را ندارید."
            if row["status"] == "cancelled":
                return False, "این رزرو قبلاً لغو شده است."
            property_id = row["property_id"]
        else:
            row = conn.execute(
                "SELECT property_id, status FROM reservations WHERE id = ?",
                (reservation_id,)
            ).fetchone()
            if not row:
                return False, "رزرو یافت نشد."
            if row["status"] == "cancelled":
                return False, "این رزرو قبلاً لغو شده است."
            property_id = row["property_id"]

        # لغو رزرو
        conn.execute(
            "UPDATE reservations SET status = 'cancelled' WHERE id = ?",
            (reservation_id,)
        )

        # بررسی آیا رزروی تاییدشده‌ی دیگری برای این اقامتگاه وجود دارد
        remaining = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations "
            "WHERE property_id = ? AND status = 'confirmed'",
            (property_id,)
        ).fetchone()["c"]

        if remaining == 0:
            conn.execute(
                "UPDATE properties SET is_reserved = 0, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (property_id,)
            )

        conn.commit()
    return True, None


# ===================== علاقه‌مندی =====================

def get_wishlist_items(user_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT w.id AS wishlist_id, p.id, p.title, p.location, p.price_per_night, p.images "
            "FROM wishlist w JOIN properties p ON w.property_id = p.id "
            "WHERE w.user_id = ? ORDER BY w.added_at DESC",
            (user_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def add_to_wishlist(user_id, property_id):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO wishlist (user_id, property_id) VALUES (?, ?)",
            (user_id, property_id)
        )
        conn.commit()


def remove_from_wishlist(user_id, wishlist_id):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM wishlist WHERE id = ? AND user_id = ?",
            (wishlist_id, user_id)
        )
        conn.commit()


# ===================== نشست‌ها (Sessions) =====================

SESSION_TTL_HOURS = 24


def create_session(user_id):
    session_id = secrets_safe_uuid()
    expires_at = (datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
            (session_id, user_id, expires_at)
        )
        conn.commit()
    return session_id


def get_user_by_session(session_id):
    """بررسی نشست و بازگرداندن user_id در صورت معتبر بودن."""
    if not session_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id, expires_at FROM sessions WHERE id = ?",
            (session_id,)
        ).fetchone()
    if not row:
        return None
    # بررسی انقضا
    if row["expires_at"]:
        try:
            expires = datetime.fromisoformat(row["expires_at"])
            if datetime.utcnow() > expires:
                delete_session(session_id)
                return None
        except ValueError:
            return None
    return row["user_id"]


def delete_session(session_id):
    if not session_id:
        return
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()


def secrets_safe_uuid():
    """تولید UUID امن با secrets (به‌جای uuid.uuid4 که امن نیست)."""
    import secrets as _s
    return str(_s.token_hex(16))


# ===================== داشبورد ادمین =====================

def get_admin_stats():
    """گرفتن آمار کلی برای داشبورد ادمین."""
    with get_db() as conn:
        users_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        properties_count = conn.execute("SELECT COUNT(*) AS c FROM properties").fetchone()["c"]
        messages_count = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"]
        unread_count = conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE is_read = 0"
        ).fetchone()["c"]
        comments_count = conn.execute("SELECT COUNT(*) AS c FROM comments").fetchone()["c"]
        hosts_count = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE account_type = 'host'"
        ).fetchone()["c"]
        reservations_count = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE status = 'confirmed'"
        ).fetchone()["c"]
        reservations_total_count = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations"
        ).fetchone()["c"]
        cancelled_count = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE status = 'cancelled'"
        ).fetchone()["c"]
        reserved_properties_count = conn.execute(
            "SELECT COUNT(*) AS c FROM properties WHERE is_reserved = 1"
        ).fetchone()["c"]
        revenue_row = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) AS s FROM reservations "
            "WHERE status = 'confirmed'"
        ).fetchone()
        total_revenue = float(revenue_row["s"] or 0)
    return {
        "users": users_count,
        "properties": properties_count,
        "messages": messages_count,
        "unread_messages": unread_count,
        "comments": comments_count,
        "hosts": hosts_count,
        "reservations": reservations_count,
        "reservations_total": reservations_total_count,
        "reservations_cancelled": cancelled_count,
        "reserved_properties": reserved_properties_count,
        "total_revenue": total_revenue,
    }
