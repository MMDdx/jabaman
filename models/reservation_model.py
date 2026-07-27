# models/reservation_model.py
"""توابع دامنه‌ی رزرو — محاسبه قیمت، بررسی هم‌پوشانی، و CRUD رزرو.

شامل:
- _parse_date (helper داخلی)
- calculate_reservation_price
- is_property_available
- _generate_reservation_code (helper داخلی)
- create_reservation / get_reservation
- get_user_reservations / get_reservations_for_property
- get_all_reservations / cancel_reservation
"""
import secrets
import string
from datetime import datetime, date

from ._shared import get_db, _dict, DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT
from .property_model import get_property


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
