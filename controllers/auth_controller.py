# controllers/auth_controller.py
"""کنترلر احراز هویت — ورود، ثبت‌نام، خروج.

مسیرهای تحت پوشش:
- GET  /login, /register, /logout         → نمایش صفحات
- POST /login, /register, /logout         → پردازش فرم

توابع:
- get_login_page(user_id)         → نمایش صفحه ورود
- get_signup_page(user_id)        → نمایش صفحه ثبت‌نام
- handle_register(params, ...)    → پردازش ثبت‌نام
- handle_login(params, ...)       → پردازش ورود
- handle_logout(user_id)          → خروج (هم GET هم POST)
"""
import sqlite3
from http.cookies import SimpleCookie

import models
from utils.security import hash_password, verify_password
from views import (
    generate_login_page,
    generate_signup_page,
    generate_logout_page,
    generate_error_page,
)

from ._shared import Response, EMAIL_REGEX


# ========================
#  GET handlers
# ========================
def get_login_page(user_id):
    """نمایش صفحه‌ی ورود."""
    return Response.html(200, generate_login_page(user_id))


def get_signup_page(user_id):
    """نمایش صفحه‌ی ثبت‌نام."""
    return Response.html(200, generate_signup_page(user_id))


# ========================
#  POST handlers
# ========================
def handle_register(params, wants_json=False):
    """پردازش فرم ثبت‌نام.

    اعتبارسنجی‌ها:
    - فیلدهای الزامی: first_name, last_name, email, password, confirm_password, account_type
    - ایمیل معتبر
    - رمز عبور ≥ ۸ کاراکتر
    - تطابق رمز و تکرار آن
    - account_type یکی از guest/host
    """
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
    """پردازش فرم ورود.

    در صورت موفقیت:
    - نشست در DB ذخیره می‌شود.
    - کوکی HttpOnly با SameSite=Lax ست می‌شود.
    - درخواست fetch: JSON با redirect /  در غیر این صورت: redirect 303 به /.
    """
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


def handle_logout(user_id):
    """خروج — پاک‌کردن کوکی session_id.

    هم GET و هم POST به این تابع سپرده می‌شوند.
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
