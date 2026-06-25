# router.py (نسخه جدید با Dynamic Routes و صفحات خطا)

import urllib.parse
import sqlite3
from hashlib import sha256
from views import (
    generate_table_html,
    generate_catalog_html,
    generate_home_html,
    generate_edit_user_form,
    generate_edit_property_form,
    generate_property_detail,
    generate_message_detail,
    generate_error_page
)

DB_NAME = "db.sqlite"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return sha256(password.encode()).hexdigest()

# -------------------------------------------------------------------
#                توابع کمکی برای مدیریت مسیرها
# -------------------------------------------------------------------
def match_route(path, pattern):
    """
    مسیر را با الگوی حاوی بخش‌های <int:id> تطبیق می‌دهد.
    در صورت تطابق، یک dict از پارامترها برمی‌گرداند، در غیر این صورت None.
    """
    path_parts = path.strip('/').split('/')
    pattern_parts = pattern.strip('/').split('/')
    if len(path_parts) != len(pattern_parts):
        return None
    params = {}
    for pp, pat in zip(path_parts, pattern_parts):
        if pat.startswith('<') and pat.endswith('>'):
            param_type = pat[1:-1].split(':')[0]  # int یا str
            param_name = pat[1:-1].split(':')[1] if ':' in pat[1:-1] else 'id'
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

# -------------------------------------------------------------------
#                     مسیرهای GET
# -------------------------------------------------------------------
def process_get(path):
    # حذف query string (اگر باشد)
    path = path.split('?')[0]

    # ----------- صفحات اصلی -----------
    if path == "/" or path == "":
        return view_home()
    elif path == "/catalog":
        return view_catalog()
    elif path == "/admin/users":
        return view_users()
    elif path == "/admin/messages":
        return view_messages()
    elif path == "/admin/properties":
        return view_properties()

    # ----------- نمایش تکی -----------
    # /property/<int:id>
    params = match_route(path, "/property/<int:id>")
    if params:
        return view_property_detail(params['id'])

    # /message/<int:id>
    params = match_route(path, "/message/<int:id>")
    if params:
        return view_message_detail(params['id'])

    # ----------- فرم‌های ویرایش -----------
    # /admin/users/<int:id>/edit
    params = match_route(path, "/admin/users/<int:id>/edit")
    if params:
        return edit_user_form(params['id'])

    # /admin/properties/<int:id>/edit
    params = match_route(path, "/admin/properties/<int:id>/edit")
    if params:
        return edit_property_form(params['id'])

    # ----------- اگر هیچ‌کدام نبود، 404 سفارشی -----------
    return None  # اجازه می‌دهیم server.py خودش صفحه 404 را مدیریت کند (یا از router.error_404 استفاده می‌کنیم)

# -------------------------------------------------------------------
#                     مسیرهای POST
# -------------------------------------------------------------------
def process_post(path, body):
    path = path.split('?')[0]
    params = urllib.parse.parse_qs(body.decode()) if body else {}

    # مسیرهای ثابت
    if path == "/contact":
        return handle_contact(params)
    elif path == "/register":
        return handle_register(params)
    elif path == "/add-property":
        return handle_add_property(params)

    # مسیرهای ویرایش داینامیک
    route_params = match_route(path, "/admin/users/<int:id>/edit")
    if route_params:
        return handle_edit_user(params, route_params['id'])

    route_params = match_route(path, "/admin/properties/<int:id>/edit")
    if route_params:
        return handle_edit_property(params, route_params['id'])

    return 404, "text/html; charset=utf-8", generate_error_page(404)

# -------------------------------------------------------------------
#                     توابع نمایش (GET)
# -------------------------------------------------------------------
def view_home():
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, title, property_type, location, price_per_night FROM properties ORDER BY id DESC LIMIT 6"
        ).fetchall()
        conn.close()
    except Exception as e:
        rows = []
    html = generate_home_html(rows)
    return 200, "text/html; charset=utf-8", html

def view_catalog():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, title, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, description FROM properties").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    html = generate_catalog_html("کاتالوگ اقامتگاه‌ها", rows)
    return 200, "text/html; charset=utf-8", html

def view_users():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, first_name, last_name, phone, account_type, created_at FROM users").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    html = generate_table_html("کاربران", ["شناسه", "نام", "نام خانوادگی", "موبایل", "نوع حساب", "تاریخ ثبت‌نام"], rows)
    return 200, "text/html; charset=utf-8", html

def view_messages():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, fullname, email, phone, topic, message_text, is_read, created_at FROM messages").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    html = generate_table_html("پیام‌ها", ["شناسه", "فرستنده", "ایمیل", "تلفن", "موضوع", "متن", "خوانده‌شده", "تاریخ"], rows)
    return 200, "text/html; charset=utf-8", html

def view_properties():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, host_id, title, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, created_at FROM properties").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    html = generate_table_html("اقامتگاه‌ها", ["شناسه", "میزبان", "عنوان", "نوع", "موقعیت", "قیمت/شب", "ظرفیت", "اتاق", "سرویس", "تاریخ ثبت"], rows)
    return 200, "text/html; charset=utf-8", html

def view_property_detail(property_id):
    try:
        conn = get_db()
        prop = conn.execute("SELECT * FROM properties WHERE id=?", (property_id,)).fetchone()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    if not prop:
        return 404, "text/html; charset=utf-8", generate_error_page(404)
    html = generate_property_detail(prop)
    return 200, "text/html; charset=utf-8", html

def view_message_detail(message_id):
    try:
        conn = get_db()
        msg = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    if not msg:
        return 404, "text/html; charset=utf-8", generate_error_page(404)
    html = generate_message_detail(msg)
    return 200, "text/html; charset=utf-8", html

def edit_user_form(user_id):
    try:
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    if not user:
        return 404, "text/html; charset=utf-8", generate_error_page(404)
    html = generate_edit_user_form(user)
    return 200, "text/html; charset=utf-8", html

def edit_property_form(property_id):
    try:
        conn = get_db()
        prop = conn.execute("SELECT * FROM properties WHERE id=?", (property_id,)).fetchone()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))
    if not prop:
        return 404, "text/html; charset=utf-8", generate_error_page(404)
    html = generate_edit_property_form(prop)
    return 200, "text/html; charset=utf-8", html

# -------------------------------------------------------------------
#                     مدیریت POST (درج و ویرایش)
# -------------------------------------------------------------------
def handle_contact(params):
    # ... (همان کد قبلی)
    fullname = params.get('fullname', [''])[0]
    email = params.get('email', [''])[0]
    phone = params.get('phone', [''])[0]
    topic = params.get('topic', [''])[0]
    message_text = params.get('message_text', [''])[0]
    if not fullname or not message_text:
        return 400, "text/html; charset=utf-8", "نام و متن پیام الزامی است."
    try:
        conn = get_db()
        conn.execute("INSERT INTO messages (fullname, email, phone, topic, message_text) VALUES (?,?,?,?,?)",
                     (fullname, email, phone, topic, message_text))
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "پیام با موفقیت ثبت شد. <a href='/contact'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

def handle_register(params):
    # ... (همان کد قبلی)
    first_name = params.get('first_name', [''])[0]
    last_name = params.get('last_name', [''])[0]
    phone = params.get('phone', [''])[0]
    password = params.get('password', [''])[0]
    confirm_password = params.get('confirm_password', [''])[0]
    account_type = params.get('account_type', [''])[0]
    if not all([first_name, last_name, phone, password, confirm_password, account_type]):
        return 400, "text/html; charset=utf-8", "فیلدهای الزامی را پر کنید."
    if password != confirm_password:
        return 400, "text/html; charset=utf-8", "رمز عبور و تکرار آن مطابقت ندارند."
    if len(password) < 8:
        return 400, "text/html; charset=utf-8", "رمز عبور باید حداقل ۸ کاراکتر باشد."
    if account_type not in ('guest', 'host'):
        return 400, "text/html; charset=utf-8", "نوع حساب نامعتبر است."
    try:
        conn = get_db()
        conn.execute("INSERT INTO users (first_name, last_name, phone, password_hash, account_type) VALUES (?,?,?,?,?)",
                     (first_name, last_name, phone, hash_password(password), account_type))
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "ثبت‌نام با موفقیت انجام شد. <a href='/register'>بازگشت</a>"
    except sqlite3.IntegrityError:
        return 400, "text/html; charset=utf-8", "این شماره موبایل قبلاً ثبت شده است."
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

def handle_add_property(params):
    # ... (همان کد قبلی)
    host_id = params.get('host_id', ['1'])[0]
    title = params.get('title', [''])[0]
    description = params.get('description', [''])[0]
    property_type = params.get('property_type', [''])[0]
    location = params.get('location', [''])[0]
    price_per_night = params.get('price_per_night', ['0'])[0]
    max_guests = params.get('max_guests', ['1'])[0]
    bedrooms = params.get('bedrooms', ['0'])[0]
    bathrooms = params.get('bathrooms', ['0'])[0]
    if not all([title, property_type, location, price_per_night, max_guests]):
        return 400, "text/html; charset=utf-8", "فیلدهای الزامی را پر کنید."
    try:
        conn = get_db()
        conn.execute("""INSERT INTO properties (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                     (host_id, title, description, property_type, location, float(price_per_night), int(max_guests), int(bedrooms), int(bathrooms)))
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "اقامتگاه با موفقیت اضافه شد. <a href='/add-property'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

def handle_edit_user(params, user_id):
    first_name = params.get('first_name', [''])[0]
    last_name = params.get('last_name', [''])[0]
    phone = params.get('phone', [''])[0]
    account_type = params.get('account_type', [''])[0]
    if not all([first_name, last_name, phone, account_type]):
        return 400, "text/html; charset=utf-8", "فیلدهای الزامی را پر کنید."
    if account_type not in ('guest', 'host'):
        return 400, "text/html; charset=utf-8", "نوع حساب نامعتبر است."
    try:
        conn = get_db()
        conn.execute("UPDATE users SET first_name=?, last_name=?, phone=?, account_type=? WHERE id=?",
                     (first_name, last_name, phone, account_type, user_id))
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "کاربر با موفقیت ویرایش شد. <a href='/admin/users'>بازگشت</a>"
    except sqlite3.IntegrityError:
        return 400, "text/html; charset=utf-8", "این شماره موبایل قبلاً ثبت شده است."
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

def handle_edit_property(params, property_id):
    title = params.get('title', [''])[0]
    description = params.get('description', [''])[0]
    property_type = params.get('property_type', [''])[0]
    location = params.get('location', [''])[0]
    price_per_night = params.get('price_per_night', ['0'])[0]
    max_guests = params.get('max_guests', ['1'])[0]
    bedrooms = params.get('bedrooms', ['0'])[0]
    bathrooms = params.get('bathrooms', ['0'])[0]
    if not all([title, property_type, location, price_per_night, max_guests]):
        return 400, "text/html; charset=utf-8", "فیلدهای الزامی را پر کنید."
    try:
        conn = get_db()
        conn.execute("""UPDATE properties SET title=?, description=?, property_type=?, location=?, price_per_night=?, max_guests=?, bedrooms=?, bathrooms=?
                        WHERE id=?""",
                     (title, description, property_type, location, float(price_per_night), int(max_guests), int(bedrooms), int(bathrooms), property_id))
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "اقامتگاه با موفقیت ویرایش شد. <a href='/admin/properties'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))


# در router.py اضافه کنید:
def error_404():
    return 404, "text/html; charset=utf-8", generate_error_page(404)

def error_403():
    return 403, "text/html; charset=utf-8", generate_error_page(403)

def error_500():
    return 500, "text/html; charset=utf-8", generate_error_page(500)