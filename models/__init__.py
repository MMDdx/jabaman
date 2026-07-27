# models/__init__.py
"""پکیج مدل‌ها — لایه‌ی Model در معماری MVC.

تمام دسترسی‌های دیتابیس اینجا انجام می‌شود. تقسیم‌بندی ماژول‌ها بر اساس
دامنه‌ی کاربرد (domain-driven)، مشابه پکیج controllers:

- _shared:           زیرساخت مشترک (get_db, _dict, DB_NAME, ثابت‌های پیش‌فرض)
- user_model:        کاربران و نقش‌ها (get_user, create_user, is_admin, is_host, ...)
- property_model:    CRUD اقامتگاه‌ها
- property_image_model: تصاویر اقامتگاه (MAX_PROPERTY_IMAGES, ...)
- message_model:     پیام‌های تماس با ما
- comment_model:     نظرات اقامتگاه‌ها
- reservation_model: رزرو (محاسبه قیمت، هم‌پوشانی، CRUD)
- cart_model:        سبد خرید (وابسته به reservation_model)
- wishlist_model:    لیست علاقه‌مندی‌ها
- session_model:     نشست‌های کاربری
- admin_model:       آمار داشبورد ادمین

این __init__ تمام نمادهای عمومی را re-export می‌کند تا همه‌ی consumerها
(server.py, views.py, controllers/*.py) بدون تغییر با `import models` و
`models.fn(...)` به‌صورت قبل کار کنند.
"""

# --- ثابت‌ها و زیرساخت از _shared ---
from ._shared import (
    DB_NAME,
    DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT,
    EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT,
    get_db,
    _dict,
)

# --- کاربران ---
from .user_model import (
    get_user,
    get_all_users,
    get_user_by_email,
    create_user,
    update_user,
    is_admin,
    get_user_account_type,
    is_host,
    delete_user,
)

# --- اقامتگاه‌ها ---
from .property_model import (
    get_all_properties,
    get_property,
    get_featured_properties,
    get_properties_by_host,
    create_property,
    update_property,
    delete_property,
)

# --- تصاویر اقامتگاه ---
from .property_image_model import (
    MAX_PROPERTY_IMAGES,
    get_property_images,
    get_property_image_ids,
    count_property_images,
    add_property_image,
    get_image_by_id,
    delete_property_image,
    delete_all_property_images,
    get_featured_image,
    get_featured_images_for_properties,
)

# --- پیام‌ها ---
from .message_model import (
    get_all_messages,
    get_message,
    create_message,
    mark_message_read,
    delete_message,
)

# --- نظرات ---
from .comment_model import (
    get_comments_for_property,
    get_all_comments,
    get_comment,
    delete_comment,
    add_comment,
)

# --- رزرو ---
from .reservation_model import (
    calculate_reservation_price,
    is_property_available,
    create_reservation,
    get_reservation,
    get_user_reservations,
    get_reservations_for_property,
    get_all_reservations,
    cancel_reservation,
)

# --- سبد خرید ---
from .cart_model import (
    get_cart_items,
    add_to_cart,
    remove_from_cart,
    clear_cart,
)

# --- علاقه‌مندی ---
from .wishlist_model import (
    get_wishlist_items,
    add_to_wishlist,
    remove_from_wishlist,
)

# --- نشست‌ها ---
from .session_model import (
    SESSION_TTL_HOURS,
    create_session,
    get_user_by_session,
    delete_session,
    secrets_safe_uuid,
)

# --- داشبورد ادمین ---
from .admin_model import (
    get_admin_stats,
)


__all__ = [
    # _shared
    "DB_NAME",
    "DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT",
    "EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT",
    "get_db",
    "_dict",
    # user
    "get_user",
    "get_all_users",
    "get_user_by_email",
    "create_user",
    "update_user",
    "is_admin",
    "get_user_account_type",
    "is_host",
    "delete_user",
    # property
    "get_all_properties",
    "get_property",
    "get_featured_properties",
    "get_properties_by_host",
    "create_property",
    "update_property",
    "delete_property",
    # property_image
    "MAX_PROPERTY_IMAGES",
    "get_property_images",
    "get_property_image_ids",
    "count_property_images",
    "add_property_image",
    "get_image_by_id",
    "delete_property_image",
    "delete_all_property_images",
    "get_featured_image",
    "get_featured_images_for_properties",
    # message
    "get_all_messages",
    "get_message",
    "create_message",
    "mark_message_read",
    "delete_message",
    # comment
    "get_comments_for_property",
    "get_all_comments",
    "get_comment",
    "delete_comment",
    "add_comment",
    # reservation
    "calculate_reservation_price",
    "is_property_available",
    "create_reservation",
    "get_reservation",
    "get_user_reservations",
    "get_reservations_for_property",
    "get_all_reservations",
    "cancel_reservation",
    # cart
    "get_cart_items",
    "add_to_cart",
    "remove_from_cart",
    "clear_cart",
    # wishlist
    "get_wishlist_items",
    "add_to_wishlist",
    "remove_from_wishlist",
    # session
    "SESSION_TTL_HOURS",
    "create_session",
    "get_user_by_session",
    "delete_session",
    "secrets_safe_uuid",
    # admin
    "get_admin_stats",
]
