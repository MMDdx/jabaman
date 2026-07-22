# router.py
"""لایه‌ی Controller در معماری MVC — نگاشت مسیرها به توابع هندلر.

تغییرات نسخه‌ی فعلی:
- صفحات contact / login / signup / add-property از static به templates منتقل شدند
  و حالا از طریق router سرو می‌شوند تا user_id به آن‌ها پاس شود.
  به‌این‌ترتیب navbar در همه‌ی صفحات یکپارچه است و وضعیت ورود کاربر را نشان می‌دهد.
- توابع views.py همگی user_id می‌گیرند.
- logout از یک قالب با JS خارجی (logout.js) استفاده می‌کند به‌جای inline script.
- login_redirect هم از قالب با JS خارجی (login_redirect.js) استفاده می‌کند.
"""
import json
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
    generate_login_redirect_page,
    generate_contact_page, generate_login_page, generate_signup_page,
    generate_add_property_page, generate_logout_page,
    generate_admin_dashboard,
    generate_checkout_page, generate_checkout_success_page,
    generate_reservations_page,
)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def _parse_form_body(body, content_type=None):
    """تجزیه‌ی بدنه‌ی POST با پشتیبانی از هر دو فرمت:

    1. application/x-www-form-urlencoded  (پیش‌فرض HTML forms)
    2. multipart/form-data  (FormData در fetch)

    خروجی: dict شبیه parse_qs با مقادیر لیست.
    """
    if not body:
        return {}

    if isinstance(body, bytes):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return {}
    else:
        text = body

    # اگر multipart است
    if (content_type and "multipart/form-data" in content_type.lower()) or \
       (not content_type and "------" in text[:200] and "Content-Disposition" in text[:500]):
        return _parse_multipart(body, content_type)

    # در غیر این صورت URL-encoded
    return urllib.parse.parse_qs(text)


def _parse_multipart(body, content_type):
    """پارسر ساده‌ی multipart/form-data (بدون کتابخانه خارجی)."""
    if isinstance(body, str):
        body = body.encode("utf-8")

    # پیدا کردن boundary از content_type یا از بدنه
    boundary = None
    if content_type:
        m = re.search(r'boundary=("?)([^";]+)\1', content_type)
        if m:
            boundary = m.group(2)

    if not boundary:
        # تلاش برای استخراج از بدنه
        m = re.match(rb'--([^\r\n]+)', body)
        if m:
            boundary = m.group(1).decode("utf-8", errors="ignore")

    if not boundary:
        return {}

    boundary_bytes = ("--" + boundary).encode("utf-8")
    parts = body.split(boundary_bytes)
    result = {}

    for part in parts:
        # حذف -- در پایان و \r\n در ابتدا/انتها
        if not part or part in (b"--\r\n", b"--", b"\r\n", b"\r\n--\r\n"):
            continue
        # حذف \r\n ابتدایی
        part = part.lstrip(b"\r\n")
        # حذف \r\n انتهایی
        if part.endswith(b"\r\n"):
            part = part[:-2]
        # پایان مارکر
        if part == b"--" or part.endswith(b"--"):
            continue

        # جداکردن headers و content با \r\n\r\n
        if b"\r\n\r\n" not in part:
            continue
        header_blob, value = part.split(b"\r\n\r\n", 1)

        # استخراج name از Content-Disposition
        m = re.search(rb'name="([^"]+)"', header_blob)
        if not m:
            continue
        name = m.group(1).decode("utf-8", errors="ignore")

        # اگر filename داشت (فایل آپلودی) → رد می‌کنیم
        if b"filename=" in header_blob:
            continue

        try:
            value_str = value.decode("utf-8")
        except UnicodeDecodeError:
            value_str = value.decode("latin-1")

        result.setdefault(name, []).append(value_str)

    return result

# کلاس کمک‌کننده برای ساخت پاسخ با هدرهای اضافی
class Response:
    """ساخت پاسخ با هدرهای اضافی (Set-Cookie, Location, ...)."""
    @staticmethod
    def html(status, body, headers=None):
        return (status, "text/html; charset=utf-8", body, headers or [])

    @staticmethod
    def json(status, payload, headers=None):
        """ساخت پاسخ JSON.

        payload یک dict است که به JSON تبدیل می‌شود.
        کاربرد اصلی: پاسخ به درخواست‌های fetch از فرم‌های login/signup.
        """
        h = list(headers or [])
        body = json.dumps(payload, ensure_ascii=False)
        return (status, "application/json; charset=utf-8", body, h)

    @staticmethod
    def redirect(location, headers=None):
        h = list(headers or [])
        h.append(("Location", location))
        return (303, "text/html; charset=utf-8", "", h)

    @staticmethod
    def login_required():
        return Response.html(200, generate_login_redirect_page())

    @staticmethod
    def forbidden(user_id=None):
        return Response.html(403, generate_error_page(403, user_id=user_id))


def _wants_json(headers):
    """تشخیص اینکه آیا کلاینت JSON می‌خواهد (درخواست fetch/XHR).

    معیارها:
    - هدر Accept شامل 'application/json' باشد، یا
    - هدر X-Requested-With برابر 'XMLHttpRequest' باشد.
    """
    if headers is None:
        return False
    accept = (headers.get("Accept") or "").lower()
    xrw = (headers.get("X-Requested-With") or "").lower()
    return "application/json" in accept or xrw == "xmlhttprequest"


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
        return Response.html(200, generate_catalog_html("کاتالوگ اقامتگاه‌ها", properties, user_id))

    # ---------- صفحات فرم عمومی (حالا از طریق router سرو می‌شوند) ----------
    if path == "/contact":
        return Response.html(200, generate_contact_page(user_id))

    if path == "/login":
        return Response.html(200, generate_login_page(user_id))

    if path == "/register":
        return Response.html(200, generate_signup_page(user_id))

    if path == "/add-property":
        # در صورت عدم ورود، صفحه‌ی ریدایرکت لاگین نمایش بده
        if not _require_login(user_id):
            return Response.login_required()
        return Response.html(200, generate_add_property_page(user_id))

    # ---------- ورود / ثبت‌نام / خروج ----------
    if path == "/logout":
        return handle_logout_get(user_id)

    # ---------- مسیرهای نیازمند ورود ----------
    if path == "/cart":
        if not _require_login(user_id):
            return Response.login_required()
        items = models.get_cart_items(user_id)
        return Response.html(200, generate_cart_page(items, user_id))

    if path == "/checkout":
        if not _require_login(user_id):
            return Response.login_required()
        items = models.get_cart_items(user_id)
        if not items:
            return Response.redirect("/cart")
        return Response.html(200, generate_checkout_page(items, user_id))

    if path == "/reservations":
        if not _require_login(user_id):
            return Response.login_required()
        reservations = models.get_user_reservations(user_id)
        return Response.html(200, generate_reservations_page(reservations, user_id))

    if path == "/wishlist":
        if not _require_login(user_id):
            return Response.login_required()
        items = models.get_wishlist_items(user_id)
        return Response.html(200, generate_wishlist_page(items, user_id))

    # ---------- مسیرهای ادمین ----------
    if path == "/admin":
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        stats = models.get_admin_stats()
        # آخرین پیام‌ها و نظرات برای داشبورد
        recent_messages = models.get_all_messages()[:5]
        recent_comments = models.get_all_comments()[:5]
        return Response.html(200, generate_admin_dashboard(
            stats, recent_messages, recent_comments, user_id
        ))

    if path == "/admin/users":
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        users = models.get_all_users()
        # نگاشت کلیدهای انگلیسی dict به کلیدهای فارسی مطابق با عناوین ستون‌ها
        formatted = []
        for u in users:
            row = dict(u)
            row["شناسه"] = u.get("id")
            row["نام"] = u.get("first_name")
            row["نام خانوادگی"] = u.get("last_name")
            row["ایمیل"] = u.get("email")
            row["موبایل"] = u.get("phone") or "—"
            row["نوع حساب"] = "میزبان" if u.get("account_type") == "host" else "مهمان"
            row["ادمین"] = "بله" if u.get("is_admin") else "—"
            row["تاریخ ثبت‌نام"] = u.get("created_at")
            formatted.append(row)
        return Response.html(200, generate_table_html(
            "کاربران",
            ["شناسه", "نام", "نام خانوادگی", "ایمیل", "موبایل", "نوع حساب", "ادمین", "تاریخ ثبت‌نام"],
            formatted, user_id
        ))

    if path == "/admin/messages":
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        messages = models.get_all_messages()
        formatted = []
        for m in messages:
            row = dict(m)
            row["شناسه"] = m.get("id")
            row["فرستنده"] = m.get("fullname")
            row["ایمیل"] = m.get("email") or "—"
            row["تلفن"] = m.get("phone") or "—"
            row["موضوع"] = m.get("topic") or "—"
            # متن کامل پیام در صفحه‌ی جزئیات است؛ اینجا فقط پیش‌نمایش کوتاه
            text = m.get("message_text") or ""
            row["متن"] = (text[:60] + "…") if len(text) > 60 else text
            row["خوانده‌شده"] = "✓ بله" if m.get("is_read") else "✗ خیر"
            row["تاریخ"] = m.get("created_at")
            formatted.append(row)
        return Response.html(200, generate_table_html(
            "پیام‌ها",
            ["شناسه", "فرستنده", "ایمیل", "تلفن", "موضوع", "متن", "خوانده‌شده", "تاریخ"],
            formatted, user_id
        ))

    if path == "/admin/properties":
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        properties = models.get_all_properties()
        formatted = []
        for p in properties:
            row = dict(p)
            row["شناسه"] = p.get("id")
            row["میزبان"] = p.get("host_id")
            row["عنوان"] = p.get("title")
            row["نوع"] = p.get("property_type")
            row["موقعیت"] = p.get("location")
            row["قیمت/شب"] = f"{float(p.get('price_per_night') or 0):,.0f}"
            row["ظرفیت"] = p.get("max_guests")
            row["اتاق"] = p.get("bedrooms")
            row["سرویس"] = p.get("bathrooms")
            row["تاریخ ثبت"] = p.get("created_at")
            formatted.append(row)
        return Response.html(200, generate_table_html(
            "اقامتگاه‌ها",
            ["شناسه", "میزبان", "عنوان", "نوع", "موقعیت", "قیمت/شب", "ظرفیت", "اتاق", "سرویس", "تاریخ ثبت"],
            formatted, user_id
        ))

    if path == "/admin/comments":
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        comments = models.get_all_comments()
        formatted = []
        for c in comments:
            row = dict(c)
            row["شناسه"] = c.get("id")
            row["کاربر"] = c.get("user_name")
            row["اقامتگاه"] = c.get("property_title")
            row["متن نظر"] = c.get("comment_text")
            row["امتیاز"] = f"{c.get('rating', 0)} ★"
            row["تاریخ"] = c.get("created_at")
            formatted.append(row)
        return Response.html(200, generate_table_html(
            "نظرات",
            ["شناسه", "کاربر", "اقامتگاه", "متن نظر", "امتیاز", "تاریخ"],
            formatted, user_id
        ))

    # ---------- مسیرهای داینامیک ----------
    params = match_route(path, "/property/<int:id>")
    if params:
        prop = models.get_property(params['id'])
        if not prop:
            return Response.html(404, generate_error_page(404, user_id=user_id))
        comments = models.get_comments_for_property(params['id'])
        return Response.html(200, generate_property_detail(prop, comments, user_id))

    params = match_route(path, "/message/<int:id>")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        msg = models.get_message(params['id'])
        if not msg:
            return Response.html(404, generate_error_page(404, user_id=user_id))
        # علامت‌گذاری به‌عنوان خوانده‌شده
        models.mark_message_read(params['id'])
        return Response.html(200, generate_message_detail(msg, user_id))

    params = match_route(path, "/admin/users/<int:id>/edit")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        user = models.get_user(params['id'])
        if not user:
            return Response.html(404, generate_error_page(404, user_id=user_id))
        return Response.html(200, generate_edit_user_form(user, user_id))

    params = match_route(path, "/admin/properties/<int:id>/edit")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        prop = models.get_property(params['id'])
        if not prop:
            return Response.html(404, generate_error_page(404, user_id=user_id))
        return Response.html(200, generate_edit_property_form(prop, user_id))

    # ---------- مسیرهای حذف (ادمین) ----------
    # حذف اقامتگاه
    params = match_route(path, "/admin/properties/<int:id>/delete")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        models.delete_property(params['id'])
        return Response.redirect("/admin/properties")

    # حذف کاربر
    params = match_route(path, "/admin/users/<int:id>/delete")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        # جلوگیری از حذف خود کاربر فعلی (اختیاری)
        if params['id'] == user_id:
            return Response.html(400, "نمی‌توانید حساب خودتان را حذف کنید. "
                                     "<a href='/admin/users'>بازگشت</a>")
        models.delete_user(params['id'])
        return Response.redirect("/admin/users")

    # حذف پیام
    params = match_route(path, "/admin/messages/<int:id>/delete")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        models.delete_message(params['id'])
        return Response.redirect("/admin/messages")

    # حذف نظر
    params = match_route(path, "/admin/comments/<int:id>/delete")
    if params:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        models.delete_comment(params['id'])
        return Response.redirect("/admin/comments")

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

    # ---------- لغو رزرو ----------
    params = match_route(path, "/reservation/<int:id>/cancel")
    if params:
        if not _require_login(user_id):
            return Response.login_required()
        ok, err = models.cancel_reservation(params['id'], user_id=user_id)
        if not ok:
            return Response.html(400, generate_error_page(400, err, user_id))
        return Response.redirect("/reservations")

    return None


# ========================
#         POST
# ========================
def process_post(path, body, user_id=None, headers=None):
    path = path.split('?')[0]
    content_type = headers.get("Content-Type") if headers else None
    params = _parse_form_body(body, content_type)
    wants_json = _wants_json(headers)

    if path == "/contact":
        return handle_contact(params, wants_json=wants_json)
    if path == "/register":
        return handle_register(params, wants_json=wants_json)
    if path == "/login":
        return handle_login(params, wants_json=wants_json)
    if path == "/logout":
        return handle_logout_post(user_id)
    if path == "/add-property":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_add_property(params, user_id, wants_json=wants_json)
    if path == "/cart/add":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_add_to_cart(params, user_id)
    if path == "/checkout":
        if not _require_login(user_id):
            return Response.login_required()
        return handle_checkout(params, user_id)
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
            return Response.forbidden(user_id)
        return handle_edit_user(params, p['id'])

    p = match_route(path, "/admin/properties/<int:id>/edit")
    if p:
        if not _require_admin(user_id):
            return Response.forbidden(user_id)
        return handle_edit_property(params, p['id'])

    return Response.html(404, generate_error_page(404, user_id=user_id))


# ======================== handler functions ========================

def handle_contact(params, wants_json=False):
    fullname = params.get('fullname', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    topic = params.get('topic', [''])[0].strip()
    message_text = params.get('message_text', [''])[0].strip()

    if not fullname or not message_text:
        msg = "نام و متن پیام الزامی است."
        if wants_json:
            return Response.json(400, {"success": False, "error": msg})
        return Response.html(400, msg + " <a href='/contact'>بازگشت</a>")
    if email and not EMAIL_REGEX.match(email):
        msg = "ایمیل نامعتبر است."
        if wants_json:
            return Response.json(400, {"success": False, "error": msg})
        return Response.html(400, msg + " <a href='/contact'>بازگشت</a>")

    try:
        models.create_message(fullname, email, phone, topic, message_text)
        if wants_json:
            return Response.json(200, {"success": True, "message": "پیام با موفقیت ثبت شد."})
        return Response.html(200, "پیام با موفقیت ثبت شد. <a href='/'>بازگشت به خانه</a>")
    except Exception as e:
        if wants_json:
            return Response.json(500, {"success": False, "error": str(e)})
        return Response.html(500, generate_error_page(500, str(e)))


def handle_register(params, wants_json=False):
    first_name = params.get('first_name', [''])[0].strip()
    last_name = params.get('last_name', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    password = params.get('password', [''])[0]
    confirm_password = params.get('confirm_password', [''])[0]
    account_type = params.get('account_type', [''])[0]

    def fail(msg, status=400):
        if wants_json:
            return Response.json(status, {"success": False, "error": msg})
        return Response.html(status, msg + " <a href='/register'>بازگشت</a>")

    if not all([first_name, last_name, email, password, confirm_password, account_type]):
        return fail("فیلدهای الزامی را پر کنید.")
    if not EMAIL_REGEX.match(email):
        return fail("ایمیل نامعتبر است.")
    if password != confirm_password:
        return fail("رمز عبور و تکرار آن مطابقت ندارند.")
    if len(password) < 8:
        return fail("رمز عبور باید حداقل ۸ کاراکتر باشد.")
    if account_type not in ('guest', 'host'):
        return fail("نوع حساب نامعتبر است.")

    try:
        models.create_user(
            first_name, last_name, email,
            hash_password(password), account_type,
            phone=phone or None
        )
        if wants_json:
            return Response.json(200, {
                "success": True,
                "redirect": "/login",
                "message": "ثبت‌نام با موفقیت انجام شد."
            })
        return Response.html(200, "ثبت‌نام با موفقیت انجام شد. <a href='/login'>ورود</a>")
    except sqlite3.IntegrityError:
        return fail("این ایمیل قبلاً ثبت شده است.")
    except Exception as e:
        if wants_json:
            return Response.json(500, {"success": False, "error": str(e)})
        return Response.html(500, generate_error_page(500, str(e)))


def handle_login(params, wants_json=False):
    email = params.get('email', [''])[0].strip()
    password = params.get('password', [''])[0]

    def fail(msg, status=400):
        if wants_json:
            return Response.json(status, {"success": False, "error": msg})
        return Response.html(status, msg + " <a href='/login'>بازگشت</a>")

    if not email or not password:
        return fail("ایمیل و رمز عبور الزامی است.")

    user = models.get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        # نکته امنیتی: پیام کلی می‌دهیم تا attacker نفهمد ایمیل وجود دارد یا نه.
        return fail("ایمیل یا رمز عبور نادرست است.", status=401)

    session_id = models.create_session(user["id"])

    # ساخت کوکی HttpOnly با SameSite
    cookie = SimpleCookie()
    cookie["session_id"] = session_id
    cookie["session_id"]["path"] = "/"
    cookie["session_id"]["httponly"] = True
    cookie["session_id"]["samesite"] = "Lax"
    cookie["session_id"]["max-age"] = 3600 * 24  # یک روز

    headers = [("Set-Cookie", cookie["session_id"].OutputString())]

    if wants_json:
        # برای fetch: JSON با موفقیت + redirect
        return Response.json(200, {
            "success": True,
            "redirect": "/"
        }, headers)
    return Response.redirect("/", headers)


def handle_logout_get(user_id):
    """نمایش صفحه‌ی خروج با JS خارجی برای پاک‌کردن کوکی و ریدایرکت."""
    return handle_logout_post(user_id)


def handle_logout_post(user_id):
    """پاک‌کردن نشست در سمت سرور و کلاینت.

    - سرور کوکی session_id را با max-age=0 پاک می‌کند.
    - در سمت کلاینت، فایل logout.js نیز کوکی را پاک می‌کند و سپس ریدایرکت می‌کند.
    - به‌جای inline script، از templates/logout.html + static/js/logout.js استفاده می‌شود.
    """
    # (اختیاری) پاک‌کردن session از DB — فعلاً فقط کوکی پاک می‌شود
    # if user_id:
    #     models.delete_sessions_for_user(user_id)

    # هدر Set-Cookie برای پاک‌کردن کوکی
    cookie = SimpleCookie()
    cookie["session_id"] = ""
    cookie["session_id"]["path"] = "/"
    cookie["session_id"]["max-age"] = 0
    cookie["session_id"]["httponly"] = True
    cookie["session_id"]["samesite"] = "Lax"
    headers = [("Set-Cookie", cookie["session_id"].OutputString())]

    # قالب خروج — با JS خارجی
    return Response.html(200, generate_logout_page(), headers)


def handle_add_property(params, user_id, wants_json=False):
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

    def fail(msg, status=400):
        if wants_json:
            return Response.json(status, {"success": False, "error": msg})
        return Response.html(status, msg + " <a href='/add-property'>بازگشت</a>")

    if not all([title, property_type, location, price_per_night, max_guests]):
        return fail("فیلدهای الزامی را پر کنید.")

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
        if wants_json:
            return Response.json(200, {"success": True, "redirect": "/catalog"})
        return Response.redirect("/catalog")
    except ValueError as e:
        return fail(f"ورودی نامعتبر: {e}")
    except Exception as e:
        if wants_json:
            return Response.json(500, {"success": False, "error": str(e)})
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
    """افزودن اقامتگاه به سبد با تاریخ ورود/خروج و تعداد مهمان.

    فیلدهای مورد انتظار:
    - property_id (الزامی)
    - check_in_date (YYYY-MM-DD)
    - check_out_date (YYYY-MM-DD)
    - guests (عدد)
    """
    property_id = params.get('property_id', [None])[0]
    check_in = params.get('check_in_date', [None])[0]
    check_out = params.get('check_out_date', [None])[0]
    guests = params.get('guests', ['1'])[0]

    if not property_id:
        return Response.html(400, "شناسه اقامتگاه الزامی است")

    # اعتبارسنجی تاریخ‌ها
    from datetime import datetime as _dt
    try:
        if check_in:
            _dt.strptime(check_in, "%Y-%m-%d")
        if check_out:
            _dt.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return Response.html(400, "فرمت تاریخ نامعتبر است. لطفاً از تقویم استفاده کنید.")

    if check_in and check_out and check_out <= check_in:
        return Response.html(400, "تاریخ خروج باید بعد از تاریخ ورود باشد.")

    try:
        guests_int = int(guests or 1)
        if guests_int < 1:
            guests_int = 1
    except ValueError:
        guests_int = 1

    try:
        models.add_to_cart(user_id, property_id, check_in, check_out, guests_int)
        return Response.redirect("/cart")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_checkout(params, user_id):
    """پرداخت نهایی — برای هر آیتم سبد، یک رزرو ایجاد می‌کند.

    مراحل:
    1. گرفتن آیتم‌های سبد خرید کاربر.
    2. برای هر آیتم، بررسی در دسترس بودن اقامتگاه و ایجاد رزرو.
    3. در صورت خطا برای یک آیتم، رزرو بقیه انجام می‌شود و خطا به کاربر نشان داده می‌شود.
    4. در صورت موفقیت کامل، سبد خرید پاک می‌شود و به صفحه‌ی موفقیت هدایت می‌شود.
    """
    items = models.get_cart_items(user_id)
    if not items:
        return Response.redirect("/cart")

    created_reservations = []
    errors = []

    for item in items:
        property_id = item.get("property_id")
        check_in = item.get("check_in_date")
        check_out = item.get("check_out_date")
        guests = item.get("guests") or 1
        title = item.get("title") or f"#{property_id}"

        if not check_in or not check_out:
            errors.append(f"برای «{title}» تاریخ ورود و خروج مشخص نشده است.")
            continue

        reservation_id, err = models.create_reservation(
            user_id, property_id, check_in, check_out, guests
        )
        if err:
            errors.append(f"برای «{title}»: {err}")
        else:
            created_reservations.append(reservation_id)

    # پاک کردن آیتم‌های سبد که رزرو شدند
    if created_reservations:
        models.clear_cart(user_id)

    if errors and not created_reservations:
        # همه‌ی آیتم‌ها خطا داشتند
        return Response.html(400, generate_error_page(
            400, "؛ ".join(errors), user_id
        ))

    # موفقیت (کامل یا جزئی) — نمایش صفحه‌ی موفقیت
    return Response.html(200, generate_checkout_success_page(
        created_reservations, errors, user_id
    ))


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
