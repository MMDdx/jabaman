# router.py
"""لایه‌ی Dispatcher — نگاشت URLها به کنترلرهای پکیج `controllers/`.

این فایل قبلاً یک فایل ۱۲۰۰+ خطی بود که نقش Controller را به‌تنهایی ایفا می‌کرد.
از نسخه‌ی فعلی، لاجیک به فولدر `controllers/` با تقسیم‌بندی domain-driven منتقل شده است:

    controllers/
        _shared.py             → utilityهای مشترک
        page_controller.py     → صفحات عمومی GET
        auth_controller.py     → ورود / ثبت‌نام / خروج
        admin_controller.py    → پنل ادمین
        property_controller.py → افزودن/حذف تصویر اقامتگاه
        cart_controller.py     → سبد خرید و checkout
        wishlist_controller.py → لیست علاقه‌مندی‌ها
        comment_controller.py  → ثبت نظر
        reservation_controller.py → لغو رزرو
        message_controller.py  → تماس با ما

router.py فقط دو نقش دارد:
1) dispatch: ترجمه‌ی path به فراخوانی تابع کنترلر مناسب
2) error helpers: error_404 / error_403 / error_500 برای server.py

backward-compatibility: server.py بدون هیچ تغییری کار می‌کند چون همچنان
می‌تواند router.process_get / router.process_post / router.error_* را صدا بزند.
"""
import os
import sys

# اطمینان از اینکه مسیر پروژه در sys.path است
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from views import generate_error_page

from controllers import (
    Response,
    match_route,
    parse_form_body,
    wants_json,
    require_login,
    require_admin,
)
from controllers import page_controller
from controllers import auth_controller
from controllers import admin_controller
from controllers import property_controller
from controllers import cart_controller
from controllers import wishlist_controller
from controllers import comment_controller
from controllers import reservation_controller
from controllers import message_controller


# ========================
#         GET
# ========================
def process_get(path, user_id=None):
    """Dispatch مسیرهای GET به کنترلرهای مناسب.

    خروجی: ۴تایی (status, content_type, body, headers) یا None
    (اگر None باشد، server.py به فایل استاتیک یا ۴۰۴ می‌رود).
    """
    path = path.split('?')[0]

    # ---------- صفحه اصلی ----------
    if path == "/" or path == "":
        return page_controller.home(user_id)

    # ---------- کاتالوگ ----------
    if path == "/catalog":
        return page_controller.catalog(user_id)

    # ---------- صفحات فرم عمومی ----------
    if path == "/contact":
        return page_controller.contact_page(user_id)

    if path == "/login":
        return auth_controller.get_login_page(user_id)

    if path == "/register":
        return auth_controller.get_signup_page(user_id)

    if path == "/add-property":
        return page_controller.add_property_page(user_id)

    # ---------- ورود / ثبت‌نام / خروج ----------
    if path == "/logout":
        return auth_controller.handle_logout(user_id)

    # ---------- مسیرهای نیازمند ورود ----------
    if path == "/cart":
        return page_controller.cart_page(user_id)

    if path == "/checkout":
        return page_controller.checkout_page(user_id)

    if path == "/reservations":
        return page_controller.reservations_page(user_id)

    if path == "/wishlist":
        return page_controller.wishlist_page(user_id)

    # ---------- مسیرهای ادمین ----------
    if path == "/admin":
        return admin_controller.dashboard(user_id)

    if path == "/admin/users":
        return admin_controller.list_users(user_id)

    if path == "/admin/messages":
        return admin_controller.list_messages(user_id)

    if path == "/admin/properties":
        return admin_controller.list_properties(user_id)

    if path == "/admin/comments":
        return admin_controller.list_comments(user_id)

    if path == "/admin/reservations":
        return admin_controller.list_reservations(user_id)

    # ---------- مسیرهای داینامیک ----------
    params = match_route(path, "/property/<int:id>")
    if params:
        return page_controller.property_detail(params['id'], user_id)

    params = match_route(path, "/message/<int:id>")
    if params:
        return page_controller.message_detail(params['id'], user_id)

    params = match_route(path, "/admin/users/<int:id>/edit")
    if params:
        return admin_controller.edit_user_form(params['id'], user_id)

    params = match_route(path, "/admin/properties/<int:id>/edit")
    if params:
        return admin_controller.edit_property_form(params['id'], user_id)

    # ---------- مسیرهای حذف (ادمین) ----------
    params = match_route(path, "/admin/properties/<int:id>/delete")
    if params:
        return admin_controller.delete_property(params['id'], user_id)

    params = match_route(path, "/admin/users/<int:id>/delete")
    if params:
        return admin_controller.delete_user(params['id'], user_id)

    params = match_route(path, "/admin/messages/<int:id>/delete")
    if params:
        return admin_controller.delete_message(params['id'], user_id)

    params = match_route(path, "/admin/comments/<int:id>/delete")
    if params:
        return admin_controller.delete_comment(params['id'], user_id)

    # ---------- لغو رزرو ----------
    params = match_route(path, "/reservation/<int:id>/cancel")
    if params:
        return reservation_controller.cancel_reservation(params['id'], user_id)

    params = match_route(path, "/admin/reservations/<int:id>/cancel")
    if params:
        return admin_controller.cancel_reservation(params['id'], user_id)

    # ---------- حذف آیتم از cart/wishlist ----------
    params = match_route(path, "/cart/<int:id>/remove")
    if params:
        return cart_controller.remove_from_cart(params['id'], user_id)

    params = match_route(path, "/wishlist/<int:id>/remove")
    if params:
        return wishlist_controller.remove_from_wishlist(params['id'], user_id)

    # ---------- هیچ‌کدام → None (سرور فایل استاتیک یا ۴۰۴ را امتحان می‌کند) ----------
    return None



#         POST
def process_post(path, body, user_id=None, headers=None):
    """Dispatch مسیرهای POST به کنترلرهای مناسب.

    خروجی: همیشه یک ۴تایی (status, content_type, body, headers).
    """
    path = path.split('?')[0]
    content_type = headers.get("Content-Type") if headers else None
    params = parse_form_body(body, content_type)
    is_json = wants_json(headers)

    if path == "/contact":
        return message_controller.handle_contact(params, wants_json=is_json)

    if path == "/register":
        return auth_controller.handle_register(params, wants_json=is_json)

    if path == "/login":
        return auth_controller.handle_login(params, wants_json=is_json)

    if path == "/logout":
        return auth_controller.handle_logout(user_id)

    if path == "/add-property":
        return property_controller.handle_add_property(params, user_id, wants_json=is_json)

    if path == "/cart/add":
        return cart_controller.handle_add_to_cart(params, user_id)

    if path == "/checkout":
        return cart_controller.handle_checkout(params, user_id)

    if path == "/wishlist/add":
        return wishlist_controller.handle_add_to_wishlist(params, user_id)

    if path == "/comment/add":
        return comment_controller.handle_add_comment(params, user_id)

    # ---------- ویرایش (ادمین) ----------
    p = match_route(path, "/admin/users/<int:id>/edit")
    if p:
        return admin_controller.handle_edit_user(params, p['id'], user_id)

    p = match_route(path, "/admin/properties/<int:id>/edit")
    if p:
        return admin_controller.handle_edit_property(params, p['id'], user_id)

    # ---------- حذف تصویر یک اقامتگاه ----------
    p = match_route(path, "/property/<int:property_id>/images/<int:image_id>/delete")
    if p:
        return property_controller.handle_delete_property_image(
            p['property_id'], p['image_id'], user_id
        )

    # ---------- هیچ‌کدام → ۴۰۴ ----------
    return Response.html(404, generate_error_page(404, user_id=user_id))


# ========================
#         error helpers
# ========================
def error_404():
    return (404, "text/html; charset=utf-8", generate_error_page(404), [])


def error_403():
    return (403, "text/html; charset=utf-8", generate_error_page(403), [])


def error_500():
    return (500, "text/html; charset=utf-8", generate_error_page(500), [])
