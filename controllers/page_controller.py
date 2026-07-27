# controllers/page_controller.py
"""کنترلر صفحات عمومی — تمام GETهای ساده‌ی سایت.

این کنترلر فقط صفحات عمومی را سرو می‌کند (نه ادمین، نه POST handler).
برای هر مسیر، یک تابع مجزا وجود دارد تا router.py بتواند تمیز dispatch کند.

مسیرهای تحت پوشش:
- GET /                                    → صفحه اصلی
- GET /catalog                             → کاتالوگ اقامتگاه‌ها
- GET /contact                             → فرم تماس
- GET /add-property                        → فرم افزودن اقامتگاه (نیازمند ورود)
- GET /cart                                → سبد خرید (نیازمند ورود)
- GET /checkout                            → صفحه‌ی تسویه (نیازمند ورود + سبد غیرخالی)
- GET /reservations                        → رزروهای کاربر (نیازمند ورود)
- GET /wishlist                            → لیست علاقه‌مندی‌ها (نیازمند ورود)
- GET /property/<int:id>                   → جزئیات اقامتگاه
- GET /message/<int:id>                    → جزئیات پیام (نیازمند ادمین)
"""
import models
from views import (
    generate_home_html,
    generate_catalog_html,
    generate_contact_page,
    generate_add_property_page,
    generate_cart_page,
    generate_checkout_page,
    generate_reservations_page,
    generate_wishlist_page,
    generate_property_detail,
    generate_message_detail,
    generate_error_page,
)

from ._shared import Response, require_login, require_admin


# ========================
#  صفحه اصلی و کاتالوگ
# ========================
def home(user_id):
    """صفحه‌ی اصلی — نمایش اقامتگاه‌های ویژه."""
    featured = models.get_featured_properties()
    return Response.html(200, generate_home_html(featured, user_id))


def catalog(user_id):
    """کاتالوگ کامل اقامتگاه‌ها."""
    properties = models.get_all_properties()
    return Response.html(200, generate_catalog_html("کاتالوگ اقامتگاه‌ها", properties, user_id))


# ========================
#  صفحات فرم عمومی
# ========================
def contact_page(user_id):
    """نمایش فرم تماس با ما."""
    return Response.html(200, generate_contact_page(user_id))


def add_property_page(user_id):
    """نمایش فرم افزودن اقامتگاه (نیازمند ورود)."""
    if not require_login(user_id):
        return Response.login_required()
    return Response.html(200, generate_add_property_page(user_id))


# ========================
#  صفحات نیازمند ورود
# ========================
def cart_page(user_id):
    """نمایش سبد خرید کاربر."""
    if not require_login(user_id):
        return Response.login_required()
    items = models.get_cart_items(user_id)
    return Response.html(200, generate_cart_page(items, user_id))


def checkout_page(user_id):
    """نمایش صفحه‌ی تسویه — نیازمند سبد غیرخالی."""
    if not require_login(user_id):
        return Response.login_required()
    items = models.get_cart_items(user_id)
    if not items:
        return Response.redirect("/cart")
    return Response.html(200, generate_checkout_page(items, user_id))


def reservations_page(user_id):
    """نمایش رزروهای کاربر."""
    if not require_login(user_id):
        return Response.login_required()
    reservations = models.get_user_reservations(user_id)
    return Response.html(200, generate_reservations_page(reservations, user_id))


def wishlist_page(user_id):
    """نمایش لیست علاقه‌مندی‌های کاربر."""
    if not require_login(user_id):
        return Response.login_required()
    items = models.get_wishlist_items(user_id)
    return Response.html(200, generate_wishlist_page(items, user_id))


# ========================
#  صفحات جزئیات
# ========================
def property_detail(property_id, user_id):
    """نمایش جزئیات یک اقامتگاه به‌همدار نظرات آن."""
    prop = models.get_property(property_id)
    if not prop:
        return Response.html(404, generate_error_page(404, user_id=user_id))
    comments = models.get_comments_for_property(property_id)
    return Response.html(200, generate_property_detail(prop, comments, user_id))


def message_detail(message_id, user_id):
    """نمایش جزئیات یک پیام — فقط ادمین.

    هنگام نمایش، پیام به‌عنوان خوانده‌شده علامت‌گذاری می‌شود.
    """
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    msg = models.get_message(message_id)
    if not msg:
        return Response.html(404, generate_error_page(404, user_id=user_id))
    # علامت‌گذاری به‌عنوان خوانده‌شده
    models.mark_message_read(message_id)
    return Response.html(200, generate_message_detail(msg, user_id))
