# models/cart_model.py
"""توابع دامنه‌ی سبد خرید.

شامل:
- get_cart_items (با محاسبه‌ی قیمت و بررسی هم‌پوشانی)
- add_to_cart / remove_from_cart / clear_cart

وابستگی به reservation_model برای calculate_reservation_price و is_property_available.
"""
from ._shared import get_db, _dict
from .reservation_model import calculate_reservation_price, is_property_available


def get_cart_items(user_id):
    """گرفتن آیتم‌های سبد خرید کاربر به‌همراه اطلاعات اقامتگاه و تاریخ/مهمان.
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
