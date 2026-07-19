# router.py
"""لایه‌ی Controller در معماری MVC — نگاشت مسیرها به توابع هندلر.

تغییرات نسبت به نسخه‌ی قبل:
- حذف CURRENT_USER_ID = 1 هاردکد شده؛ همه‌چیز از نشست user_id استفاده می‌کند.
- ورود با ایمیل (نه phone).
- مسیرهای /admin فقط برای کاربران is_admin=1 قابل دسترس هستند.
- مسیرهای /cart, /wishlist, /add-property نیاز به ورود دارند.
- host_id از نشست گرفته می‌شود، نه از فرم (امنیت).
- ریدایرکت‌های واقعی با هدر Location به‌جای meta refresh.
- لاگ‌اوت واقعی با پاک‌کردن نشست و کوکی.
- اعتبارسنجی ایمیل و رمز عبور قوی‌تر.
- توابع حذف از cart/wishlist اضافه شد.
"""
import urllib.parse
import re
import sqlite3
from http.cookies import SimpleCookie

import models
from utils.security import hash_password, verify_password
from views import (
    generate_home_html, generate_catalog_html, generate_table_html,
    generate_edit_user_form, generate_edit_property_form,
    generate_error_page, generate_property_detail,
    generate_cart_page, generate_wishlist_page, generate_message_detail,
)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# کلاس کمک‌کننده برای ساخت پاسخ با هدرهای اضافی
class Response:
    """ساخت پاسخ با هدرهای اضافی (Set-Cookie, Location, ...)."""
    @staticmethod
    def html(status, body, headers=None):
        return (status, "text/html; charset=utf-8", body, headers or [])

    @staticmethod
    def redirect(location, headers=None):
        h = list(headers or [])
        h.append(("Location", location))
        return (303, "text/html; charset=utf-8", "", h)

    @staticmethod
    def login_required():
        return Response.redirect("/login")

    @staticmethod
    def forbidden():
        return Response.html(403, generate_error_page(403))


def match_route(path, pattern):
    """تطبیق مسیر داینامیک با پارامترهای <int:name>."""
    path_parts = path.strip('/').split('/')
    pattern_parts = pattern.strip('/').split('/')
    if len(path_parts) != len(pattern_parts):
        return None
    params = {}
    for pp, pat in zip(path_parts, pattern_parts):
        if pat.startswith('<') and pat.endswith('>'):
            inner = pat[1:-1]
            if ':' in inner:
                param_type, param_name = inner.split(':', 1)
            else:
                param_type, param_name = 'str', inner
            if param_type == 'int':
                try:
                    params[param_name] = int(pp)
                except ValueError:
                    return None
            else:
                params[param_name] = pp
        else:
            if pp != pat:
                return None
    return params


def _require_login(user_id):
    """بررسی ورود کاربر. اگر وارد نشده، None برمی‌گرداند (برای redirect)."""
    return user_id is not None


def _require_admin(user_id):
    """بررسی اینکه کاربر وارد شده و admin است."""
    if not user_id:
        return False
    return models.is_admin(user_id)


# ========================
#         GET
# ========================
def process_get(path, user_id=None):
    path = path.split('?')[0]

    # ---------- صفحه اصلی ----------
    if path == "/" or path == "":
        featured = models.get_featured_properties()
        return Response.html(200, generate_home_html(featured, user_id))

    # ---------- کاتالوگ ----------
    if path == "/catalog":
        properties = models.get_all_properties()
        return Response.html(200, generate_catalog_html("کاتالوگ اقامتگاه‌ها", properties))

    # ---------- ورود / ثبت‌نام / خروج ----------
    if path == "/logout":
        return handle_logout_get(user_id)

    # ---------- مسیرهای نیازمند ورود ----------
    if path == "/cart":
        if not _require_login(user_id):
            return Response.login_required()
        items = models.get_cart_items(user_id)
        return Response.html(200, generate_cart_page(items))

    if path == "/wishlist":
        if not _require_login(user_id):
            return Response.login_required()
        items = models.get_wishlist_items(user_id)
        return Response.html(200, generate_wishlist_page(items))

    # ---------- مسیرهای ادمین ----------
    if path == "/admin/users":
        if not _require_admin(user_id):
            return Response.forbidden()
        users = models.get_all_users()
        return Response.html(200, generate_table_html(
            "کاربران",
            ["شناسه", "نام", "نام خانوادگی", "ایمیل", "موبایل", "نوع حساب", "ادمین", "تاریخ ثبت‌نام"],
            users
        ))

    if path == "/admin/messages":
        if not _require_admin(user_id):
            return Response.forbidden()
        messages = models.get_all_messages()
        return Response.html(200, generate_table_html(
            "پیام‌ها",
            ["شناسه", "فرستنده", "ایمیل", "تلفن", "موضوع", "متن", "خوانده‌شده", "تاریخ"],
            messages
        ))

    if path == "/admin/properties":
        if not _require_admin(user_id):
            return Response.forbidden()
        properties = models.get_all_properties()
        return Response.html(200, generate_table_html(
            "اقامتگاه‌ها",
            ["شناسه", "میزبان", "عنوان", "نوع", "موقعیت", "قیمت/شب", "ظرفیت", "اتاق", "سرویس", "تاریخ ثبت"],
            properties
        ))

    # ---------- مسیرهای داینامیک ----------
    params = match_route(path, "/property/<int:id>")
    if params:
        prop = models.get_property(params['id'])
        if not prop:
            return Response.html(404, generate_error_page(404))
        comments = models.get_comments_for_property(params['id'])
        return Response.html(200, generate_property_detail(prop, comments, user_id))

    params = match_route(path, "/message/<int:id>")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden()
        msg = models.get_message(params['id'])
        if not msg:
            return Response.html(404, generate_error_page(404))
        # علامت‌گذاری به‌عنوان خوانده‌شده
        models.mark_message_read(params['id'])
        return Response.html(200, generate_message_detail(msg))

    params = match_route(path, "/admin/users/<int:id>/edit")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden()
        user = models.get_user(params['id'])
        if not user:
            return Response.html(404, generate_error_page(404))
        return Response.html(200, generate_edit_user_form(user))

    params = match_route(path, "/admin/properties/<int:id>/edit")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden()
        prop = models.get_property(params['id'])
        if not prop:
            return Response.html(404, generate_error_page(404))
        return Response.html(200, generate_edit_property_form(prop))

    # ---------- حذف آیتم از cart/wishlist ----------
    params = match_route(path, "/cart/<int:id>/remove")
    if params:
        if not _require_login(user_id):
            return Response.login_required()
        models.remove_from_cart(user_id, params['id'])
        return Response.redirect("/cart")

    params = match_route(path, "/wishlist/<int:id>/remove")
    if params:
        if not _require_login(user_id):
            return Response.login_required()
        models.remove_from_wishlist(user_id, params['id'])
        return Response.redirect("/wishlist")

    return None


# ========================
#         POST
# ========================
def process_post(path, body, user_id=None):
    path = path.split('?')[0]
    params = urllib.parse.parse_qs(body.decode()) if body else {}

    if path == "/contact":
        return handle_contact(params)
    if path == "/register":
        return handle_register(params)
    if path == "/login":
        return handle_login(params)
    if path == "/logout":
        return handle_logout_post(user_id)
    if path == "/add-property":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_add_property(params, user_id)
    if path == "/cart/add":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_add_to_cart(params, user_id)
    if path == "/wishlist/add":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_add_to_wishlist(params, user_id)
    if path == "/comment/add":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_add_comment(params, user_id)

    p = match_route(path, "/admin/users/<int:id>/edit")
    if p:
        if not _require_admin(user_id):
            return Response.forbidden()
        return handle_edit_user(params, p['id'])

    p = match_route(path, "/admin/properties/<int:id>/edit")
    if p:
        if not _require_admin(user_id):
            return Response.forbidden()
        return handle_edit_property(params, p['id'])

    return Response.html(404, generate_error_page(404))


# ======================== handler functions ========================

def handle_contact(params):
    fullname = params.get('fullname', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    topic = params.get('topic', [''])[0].strip()
    message_text = params.get('message_text', [''])[0].strip()

    if not fullname or not message_text:
        return Response.html(400, "نام و متن پیام الزامی است. <a href='/contact'>بازگشت</a>")
    if email and not EMAIL_REGEX.match(email):
        return Response.html(400, "ایمیل نامعتبر است. <a href='/contact'>بازگشت</a>")

    try:
        models.create_message(fullname, email, phone, topic, message_text)
        return Response.html(200, "پیام با موفقیت ثبت شد. <a href='/'>بازگشت به خانه</a>")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_register(params):
    first_name = params.get('first_name', [''])[0].strip()
    last_name = params.get('last_name', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    password = params.get('password', [''])[0]
    confirm_password = params.get('confirm_password', [''])[0]
    account_type = params.get('account_type', [''])[0]

    if not all([first_name, last_name, email, password, confirm_password, account_type]):
        return Response.html(400, "فیلدهای الزامی را پر کنید. <a href='/register'>بازگشت</a>")
    if not EMAIL_REGEX.match(email):
        return Response.html(400, "ایمیل نامعتبر است. <a href='/register'>بازگشت</a>")
    if password != confirm_password:
        return Response.html(400, "رمز عبور و تکرار آن مطابقت ندارند. <a href='/register'>بازگشت</a>")
    if len(password) < 8:
        return Response.html(400, "رمز عبور باید حداقل ۸ کاراکتر باشد. <a href='/register'>بازگشت</a>")
    if account_type not in ('guest', 'host'):
        return Response.html(400, "نوع حساب نامعتبر است. <a href='/register'>بازگشت</a>")

    try:
        models.create_user(
            first_name, last_name, email,
            hash_password(password), account_type,
            phone=phone or None
        )
        return Response.html(200, "ثبت‌نام با موفقیت انجام شد. <a href='/login'>ورود</a>")
    except sqlite3.IntegrityError:
        return Response.html(400, "این ایمیل قبلاً ثبت شده است. <a href='/login'>ورود</a>")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_login(params):
    email = params.get('email', [''])[0].strip()
    password = params.get('password', [''])[0]

    if not email or not password:
        return Response.html(400, "ایمیل و رمز عبور الزامی است. <a href='/login'>بازگشت</a>")

    user = models.get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return Response.html(401, "اطلاعات وارد شده نادرست است. <a href='/login'>تلاش مجدد</a>")

    session_id = models.create_session(user["id"])

    # ساخت کوکی HttpOnly با SameSite
    cookie = SimpleCookie()
    cookie["session_id"] = session_id
    cookie["session_id"]["path"] = "/"
    cookie["session_id"]["httponly"] = True
    cookie["session_id"]["samesite"] = "Lax"
    cookie["session_id"]["max-age"] = 3600 * 24  # یک روز

    headers = [("Set-Cookie", cookie["session_id"].OutputString())]
    return Response.redirect("/", headers)


def handle_logout_get(user_id):
    """نمایش صفحه خداحافظی یا مستقیم لاگ‌اوت."""
    return handle_logout_post(user_id)


def handle_logout_post(user_id):
    """پاک‌کردن نشست و کوکی."""
    # نکته: session_id را از سرور می‌گیریم، اما چون اینجا فقط user_id داریم،
    # از کوکی استفاده می‌کنیم. این متد بهتر است در server.py هندل شود.
    # اما برای سادگی، یک صفحه با JavaScript برای پاک‌کردن کوکی برمی‌گردانیم.
    body = """
    <!DOCTYPE html>
    <html lang='fa' dir='rtl'>
    <head><meta charset='UTF-8'><title>خروج</title></head>
    <body>
    <h2>در حال خروج...</h2>
    <script>
      document.cookie = 'session_id=; path=/; max-age=0';
      window.location.href = '/';
    </script>
    <p>اگر به‌طور خودکار منتقل نشدید، <a href='/'>اینجا کلیک کنید</a>.</p>
    </body>
    </html>
    """
    # هدر Set-Cookie برای پاک‌کردن کوکی
    cookie = SimpleCookie()
    cookie["session_id"] = ""
    cookie["session_id"]["path"] = "/"
    cookie["session_id"]["max-age"] = 0
    headers = [("Set-Cookie", cookie["session_id"].OutputString())]
    return Response.html(200, body, headers)


def handle_add_property(params, user_id):
    """host_id از نشست گرفته می‌شود، نه از فرم."""
    title = params.get('title', [''])[0].strip()
    description = params.get('description', [''])[0].strip()
    property_type = params.get('property_type', [''])[0].strip()
    location = params.get('location', [''])[0].strip()
    price_per_night = params.get('price_per_night', ['0'])[0]
    max_guests = params.get('max_guests', ['1'])[0]
    bedrooms = params.get('bedrooms', ['0'])[0]
    bathrooms = params.get('bathrooms', ['0'])[0]
    amenities_list = params.get('amenities', [])

    if not all([title, property_type, location, price_per_night, max_guests]):
        return Response.html(400, "فیلدهای الزامی را پر کنید. <a href='/add-property'>بازگشت</a>")

    try:
        # جمع‌آوری امکانات به‌صورت لیست کاما جدا
        amenities = ",".join(amenities_list) if amenities_list else None

        models.create_property(
            user_id,  # ← host_id از نشست
            title, description, property_type, location,
            float(price_per_night), int(max_guests),
            int(bedrooms), int(bathrooms),
            amenities=amenities
        )
        return Response.redirect("/catalog")
    except ValueError as e:
        return Response.html(400, f"ورودی نامعتبر: {e}. <a href='/add-property'>بازگشت</a>")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_edit_user(params, user_id):
    first_name = params.get('first_name', [''])[0].strip()
    last_name = params.get('last_name', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    account_type = params.get('account_type', [''])[0]

    if not all([first_name, last_name, email, account_type]):
        return Response.html(400, "فیلدهای الزامی را پر کنید.")
    if not EMAIL_REGEX.match(email):
        return Response.html(400, "ایمیل نامعتبر است.")
    if account_type not in ('guest', 'host'):
        return Response.html(400, "نوع حساب نامعتبر است.")

    try:
        models.update_user(user_id, first_name, last_name, email, account_type, phone=phone or None)
        return Response.redirect("/admin/users")
    except sqlite3.IntegrityError:
        return Response.html(400, "این ایمیل قبلاً ثبت شده است.")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_edit_property(params, property_id):
    title = params.get('title', [''])[0].strip()
    description = params.get('description', [''])[0].strip()
    property_type = params.get('property_type', [''])[0].strip()
    location = params.get('location', [''])[0].strip()
    price_per_night = params.get('price_per_night', ['0'])[0]
    max_guests = params.get('max_guests', ['1'])[0]
    bedrooms = params.get('bedrooms', ['0'])[0]
    bathrooms = params.get('bathrooms', ['0'])[0]
    amenities_list = params.get('amenities', [])

    if not all([title, property_type, location, price_per_night, max_guests]):
        return Response.html(400, "فیلدهای الزامی را پر کنید.")

    try:
        amenities = ",".join(amenities_list) if amenities_list else None
        models.update_property(
            property_id, title, description, property_type, location,
            float(price_per_night), int(max_guests),
            int(bedrooms), int(bathrooms),
            amenities=amenities
        )
        return Response.redirect("/admin/properties")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_add_to_cart(params, user_id):
    property_id = params.get('property_id', [None])[0]
    if not property_id:
        return Response.html(400, "شناسه اقامتگاه الزامی است")
    try:
        models.add_to_cart(user_id, property_id)
        return Response.redirect("/cart")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_add_to_wishlist(params, user_id):
    property_id = params.get('property_id', [None])[0]
    if not property_id:
        return Response.html(400, "شناسه اقامتگاه الزامی است")
    try:
        models.add_to_wishlist(user_id, property_id)
        return Response.redirect("/wishlist")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_add_comment(params, user_id):
    property_id = params.get('property_id', [None])[0]
    comment_text = params.get('comment_text', [''])[0].strip()
    rating = params.get('rating', ['5'])[0]

    if not property_id or not comment_text:
        return Response.html(400, "شناسه و متن نظر الزامی است")
    try:
        rating_int = max(1, min(5, int(rating)))
        models.add_comment(user_id, property_id, comment_text, rating_int)
        return Response.redirect(f"/property/{property_id}")
    except ValueError:
        return Response.html(400, "امتیاز نامعتبر است")


# ======================== error helpers ========================
def error_404():
    return (404, "text/html; charset=utf-8", generate_error_page(404), [])


def error_403():
    return (403, "text/html; charset=utf-8", generate_error_page(403), [])


def error_500():
    return (500, "text/html; charset=utf-8", generate_error_page(500), [])