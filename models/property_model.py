# models/property_model.py
"""توابع دامنه‌ی اقامتگاه‌ها — مدیریت CRUD اقامتگاه‌ها.

شامل:
- get_all_properties / get_property / get_featured_properties / get_properties_by_host
- create_property / update_property / delete_property

نکته: توابع مربوط به تصاویر اقامتگاه در property_image_model.py هستند.
"""
from ._shared import (
    get_db, _dict,
    DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT,
)


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

    خروجی: شناسه‌ی اقامتگاه جدید (int) یا None در صورت خطا.
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
        cur = conn.execute(
            "INSERT INTO properties "
            "(host_id, title, description, property_type, location, price_per_night, "
            " max_guests, bedrooms, bathrooms, amenities, images, extra_guest_charge) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (host_id, title, description, property_type, location, price_per_night,
             max_guests, bedrooms, bathrooms, amenities, images, egc)
        )
        conn.commit()
        return cur.lastrowid



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
