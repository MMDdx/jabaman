# models/property_image_model.py
"""توابع دامنه‌ی تصاویر اقامتگاه.

هر اقامتگاه می‌تواند حداکثر ۳ تصویر داشته باشد.
تصاویر در جدول property_images ذخیره می‌شوند (نه در فیلد CSV).
مسیر فایل فیزیکی روی دیسک در image_path قرار می‌گیرد.

شامل:
- MAX_PROPERTY_IMAGES
- get_property_images / get_property_image_ids / count_property_images
- add_property_image / get_image_by_id
- delete_property_image / delete_all_property_images
- get_featured_image / get_featured_images_for_properties
"""
from ._shared import get_db, _dict


MAX_PROPERTY_IMAGES = 3


def get_property_images(property_id):
    """گرفتن لیست تصاویر یک اقامتگاه به ترتیب sort_order.

    خروجی: لیست dict با کلیدهای id, property_id, image_path, caption, sort_order.
    """
    if not property_id:
        return []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, property_id, image_path, caption, sort_order, created_at "
            "FROM property_images WHERE property_id = ? "
            "ORDER BY sort_order ASC, id ASC",
            (property_id,)
        ).fetchall()
    return [_dict(r) for r in rows]


def get_property_image_ids(property_id):
    """گرفتن فقط شناسه‌های تصاویر یک اقامتگاه (برای بررسی مالکیت و حذف)."""
    if not property_id:
        return []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id FROM property_images WHERE property_id = ? ORDER BY sort_order ASC, id ASC",
            (property_id,)
        ).fetchall()
    return [r["id"] for r in rows]


def count_property_images(property_id):
    """تعداد تصاویر فعلی یک اقامتگاه."""
    if not property_id:
        return 0
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM property_images WHERE property_id = ?",
            (property_id,)
        ).fetchone()
    return int(row["cnt"]) if row else 0


def add_property_image(property_id, image_path, caption=None, sort_order=None):

    if not property_id or not image_path:
        return False
    current = count_property_images(property_id)
    if current >= MAX_PROPERTY_IMAGES:
        return False
    if sort_order is None:
        sort_order = current
    with get_db() as conn:
        conn.execute(
            "INSERT INTO property_images (property_id, image_path, caption, sort_order) "
            "VALUES (?, ?, ?, ?)",
            (property_id, image_path, caption, sort_order)
        )
        conn.commit()
    return True


def get_image_by_id(image_id):
    """گرفتن یک تصویر با شناسه‌ی آن."""
    if not image_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, property_id, image_path, caption, sort_order, created_at "
            "FROM property_images WHERE id = ?",
            (image_id,)
        ).fetchone()
    return _dict(row)


def delete_property_image(image_id):
    if not image_id:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT image_path FROM property_images WHERE id = ?",
            (image_id,)
        ).fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM property_images WHERE id = ?", (image_id,))
        conn.commit()
    return row["image_path"]


def delete_all_property_images(property_id):
    """حذف همه‌ی تصاویر یک اقامتگاه از دیتابیس.

    خروجی: لیست مسیرهای فایل‌های حذف‌شده (برای حذف فیزیکی توسط caller).
    """
    if not property_id:
        return []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT image_path FROM property_images WHERE property_id = ?",
            (property_id,)
        ).fetchall()
        paths = [r["image_path"] for r in rows]
        conn.execute(
            "DELETE FROM property_images WHERE property_id = ?",
            (property_id,)
        )
        conn.commit()
    return paths


def get_featured_image(property_id):
    """گرفتن مسیر تصویر شاخص (اولین تصویر) اقامتگاه.

    اگر تصویری وجود نداشت، رشته‌ی خالی برمی‌گرداند.
    """
    if not property_id:
        return ""
    with get_db() as conn:
        row = conn.execute(
            "SELECT image_path FROM property_images WHERE property_id = ? "
            "ORDER BY sort_order ASC, id ASC LIMIT 1",
            (property_id,)
        ).fetchone()
    return row["image_path"] if row else ""


def get_featured_images_for_properties(property_ids):
    """گرفتن تصویر شاخص برای چندین اقامتگاه در یک کوئری.

    خروجی: dict با کلید = property_id و مقدار = image_path.
    اقامتگاه‌هایی که تصویر ندارند در dict نخواهند بود.
    """
    if not property_ids:
        return {}
    # استفاده از GROUP BY + MIN(id) برای گرفتن اولین تصویر هر اقامتگاه
    # (پس از ORDER BY در زیرکوئری — اما SQLite ترتیب داخل زیرکوئری را
    #  در GROUP BY حفظ نمی‌کند، پس از یک رویکرد بر اساس کمترین sort_order+id استفاده می‌کنیم).
    placeholders = ",".join("?" * len(property_ids))
    sql = (
        "SELECT pi.property_id, pi.image_path "
        "FROM property_images pi "
        "INNER JOIN ("
        "  SELECT property_id, MIN(sort_order * 1000000 + id) AS rank "
        "  FROM property_images "
        f"  WHERE property_id IN ({placeholders}) "
        "  GROUP BY property_id"
        ") first ON pi.property_id = first.property_id "
        "  AND (pi.sort_order * 1000000 + pi.id) = first.rank"
    )
    with get_db() as conn:
        rows = conn.execute(sql, property_ids).fetchall()
    return {r["property_id"]: r["image_path"] for r in rows}
