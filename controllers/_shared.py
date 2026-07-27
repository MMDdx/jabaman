# controllers/_shared.py
"""توابع و کلاس‌های مشترک بین همه‌ی کنترلرها.

این ماژول هیچ‌گونه dispatching انجام نمی‌دهد — فقط ابزارهای پایه‌ای فراهم می‌کند:

- Response:          کلاس ساخت پاسخ HTTP (html / json / redirect / forbidden / login_required)
- parse_form_body:   تجزیه‌ی بدنه‌ی POST (URL-encoded و multipart)
- wants_json:        تشخیص درخواست AJAX (fetch/XHR)
- match_route:       تطبیق مسیر داینامیک با پارامترهای <int:name>
- require_login:     بررسی ورود کاربر
- require_admin:     بررسی ادمین بودن کاربر
- image helpers:     allowed_image_filename / save_uploaded_image / delete_image_file
- EMAIL_REGEX:       الگوی اعتبارسنجی ایمیل
- MAX_IMAGE_SIZE:    حداکثر اندازه‌ی فایل آپلودی
"""
import json
import os
import re
import uuid
import urllib.parse

import models
from views import (
    generate_error_page,
    generate_login_redirect_page,
)


# ========================
#  ثابت‌های سراسری
# ========================
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "properties")
# حداکثر اندازه‌ی هر فایل: ۵ مگابایت
MAX_IMAGE_SIZE = 5 * 1024 * 1024
# پسوندهای مجاز
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# ========================
#  کلاس Response
# ========================
class Response:
    """ساخت پاسخ HTTP با هدرهای اضافی (Set-Cookie, Location, ...)."""

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


# ========================
#  تجزیه‌ی بدنه‌ی POST
# ========================
def parse_form_body(body, content_type=None):
    """تجزیه‌ی بدنه‌ی POST با پشتیبانی از هر دو فرمت:

    1. application/x-www-form-urlencoded  (پیش‌فرض HTML forms)
    2. multipart/form-data  (FormData در fetch، شامل فایل آپلودی)

    خروجی: dict شبیه parse_qs با مقادیر لیست.
    برای فایل‌های آپلودی، مقدار یک dict است:
        {"filename": "x.jpg", "data": b"..."}
    """
    if not body:
        return {}

    # اگر Content-Type مشخص می‌کند که multipart است، مستقیم به parse_multipart بفرست
    # نکته: در موارد multipart با فایل باینری، decode UTF-8 ناموفق است،
    # پس باید قبل از تلاش برای decode بررسی کنیم.
    if content_type and "multipart/form-data" in content_type.lower():
        return _parse_multipart(body, content_type)

    # اگر body از نوع bytes است، آن را به متن تبدیل کن
    if isinstance(body, bytes):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            # ممکن است multipart بدون Content-Type درست باشد؛ تلاش برای تشخیص
            if body[:50].find(b"------") != -1 and body[:200].find(b"Content-Disposition") != -1:
                return _parse_multipart(body, content_type)
            return {}
    else:
        text = body

    # تشخیص multipart بدون Content-Type (برای backward-compat)
    if not content_type and "------" in text[:200] and "Content-Disposition" in text[:500]:
        return _parse_multipart(body, content_type)

    # در غیر این صورت URL-encoded
    return urllib.parse.parse_qs(text)


def _parse_multipart(body, content_type):
    """پارسر ساده‌ی multipart/form-data (بدون کتابخانه خارجی).

    خروجی: dict با مقادیر لیست.
    - برای فیلدهای متنی: مقدار یک str است.
    - برای فایل‌های آپلودی: مقدار یک dict است:
        {"filename": "x.jpg", "data": b"..."}
    """
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

        # استخراج filename اگر وجود داشت (فایل آپلودی)
        m_fn = re.search(rb'filename="([^"]*)"', header_blob)
        if m_fn:
            filename = m_fn.group(1).decode("utf-8", errors="ignore")
            # فیلد خالی (هیچ فایلی انتخاب نشده) → نادیده بگیر
            if not filename and not value:
                continue
            result.setdefault(name, []).append({
                "filename": filename,
                "data": value
            })
            continue

        # فیلد متنی معمولی
        try:
            value_str = value.decode("utf-8")
        except UnicodeDecodeError:
            value_str = value.decode("latin-1")

        result.setdefault(name, []).append(value_str)

    return result


def wants_json(headers):
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


# ========================
#  مسیریابی و کنترل دسترسی
# ========================
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


def require_login(user_id):
    """بررسی ورود کاربر. اگر وارد نشده، False برمی‌گرداند."""
    return user_id is not None


def require_admin(user_id):
    """بررسی اینکه کاربر وارد شده و admin است."""
    if not user_id:
        return False
    return models.is_admin(user_id)


# ========================
#  تنظیمات آپلود تصاویر
# ========================
def allowed_image_filename(filename):
    """بررسی اینکه فایل با پسوند مجاز است."""
    if not filename:
        return False
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_IMAGE_EXTS


def save_uploaded_image(file_info, property_id):
    """ذخیره‌ی یک فایل آپلودی روی دیسک و بازگرداندن مسیر عمومی.

    file_info: dict با کلیدهای filename و data (bytes).
    property_id: شناسه‌ی اقامتگاه (برای ساخت نام یکتا).

    خروجی: مسیر عمومی (مثل /static/uploads/properties/p12_abc123.jpg)
    یا None در صورت خطا.
    """
    if not file_info or not isinstance(file_info, dict):
        return None
    data = file_info.get("data")
    filename = file_info.get("filename") or ""
    if not data or not filename:
        return None
    if len(data) > MAX_IMAGE_SIZE:
        return None
    if not allowed_image_filename(filename):
        return None

    # ساخت نام یکتا: p{property_id}_{uuid8}.{ext}
    ext = os.path.splitext(filename.lower())[1]
    unique_name = f"p{property_id}_{uuid.uuid4().hex[:8]}{ext}"

    # اطمینان از وجود دایرکتوری
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    except OSError:
        return None

    file_path = os.path.join(UPLOAD_DIR, unique_name)
    try:
        with open(file_path, "wb") as f:
            f.write(data)
    except OSError:
        return None

    # مسیر عمومی (همان URL)
    return f"/static/uploads/properties/{unique_name}"


def delete_image_file(image_path):
    """حذف فایل فیزیکی تصویر از روی دیسک.

    image_path: مسیر عمومی مثل /static/uploads/properties/p12_abc.jpg
    """
    if not image_path:
        return
    # فقط اجازه‌ی حذف فایل از مسیر uploads را می‌دهیم (امنیت)
    if not image_path.startswith("/static/uploads/properties/"):
        return
    rel = image_path[len("/static/"):]
    abs_path = os.path.join(BASE_DIR, "static", rel.replace("/", os.sep))
    try:
        if os.path.exists(abs_path) and os.path.isfile(abs_path):
            os.remove(abs_path)
    except OSError:
        pass


def get_text_field(params, key, default=''):
    """استخراج فیلد متنی از params (parse_qs-like).

    اگر مقدار یک dict (فایل آپلودی) باشد، default برمی‌گردد.
    اگر None باشد، default برمی‌گردد.
    در غیر این صورت، مقدار strip‌شده برمی‌گردد.
    """
    v = params.get(key)
    if not v:
        return default
    val = v[0]
    if isinstance(val, dict):
        return default  # این یک فایل است، نه متن
    if val is None:
        return default
    return val.strip() if hasattr(val, 'strip') else str(val)
