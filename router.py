# router.py
import urllib.parse
import sqlite3
from hashlib import sha256
from views import *

DB_NAME = "accommodation.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return sha256(password.encode()).hexdigest()

# ========================
#     مسیرهای GET
# ========================
def process_get(path):
    if path == "/" or path == "":
        return view_home()
    elif path == "/admin/users":
        return view_users()
    elif path == "/admin/messages":
        return view_messages()
    elif path == "/admin/properties":
        return view_properties()
    elif path == "/catalog":
        return view_catalog()

    elif path == "/admin/users/1/edit":
        return edit_user_form(1)
    elif path == "/admin/properties/1/edit":
        return edit_property_form(1)
    else:
        return None

def view_users():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, first_name, last_name, phone, account_type, created_at FROM users").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"<p>خطا: {e}</p>"

    html = generate_table_html(
        title="کاربران",
        columns=["شناسه", "نام", "نام خانوادگی", "شماره موبایل", "نوع حساب", "تاریخ ثبت‌نام"],
        rows=rows
    )
    return 200, "text/html; charset=utf-8", html

def view_messages():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, fullname, email, phone, topic, message_text, is_read, created_at FROM messages").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"<p>خطا: {e}</p>"

    html = generate_table_html(
        title="پیام‌ها",
        columns=["شناسه", "فرستنده", "ایمیل", "تلفن", "موضوع", "متن پیام", "خوانده شده", "تاریخ"],
        rows=rows
    )
    return 200, "text/html; charset=utf-8", html

def view_properties():
    try:
        conn = get_db()
        rows = conn.execute("SELECT id, host_id, title, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, created_at FROM properties").fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"<p>خطا: {e}</p>"

    html = generate_table_html(
        title="اقامتگاه‌ها",
        columns=["شناسه", "میزبان", "عنوان", "نوع", "موقعیت", "قیمت (شب)", "ظرفیت", "اتاق", "سرویس", "تاریخ ثبت"],
        rows=rows
    )
    return 200, "text/html; charset=utf-8", html

# ========================
#     مسیرهای POST
# ========================
def process_post(path, body):
    params = urllib.parse.parse_qs(body.decode()) if body else {}

    if path == "/contact":
        return handle_contact(params)
    elif path == "/register":
        return handle_register(params)
    elif path == "/add-property":
        return handle_add_property(params)
    elif path == "/admin/users/1/edit":
        return handle_edit_user(params, 1)
    elif path == "/admin/properties/1/edit":
        return handle_edit_property(params, 1)

    else:
        return 404, "text/plain", "Not Found"

def handle_contact(params):
    fullname = params.get('fullname', [''])[0]
    email = params.get('email', [''])[0]
    phone = params.get('phone', [''])[0]
    topic = params.get('topic', [''])[0]
    message_text = params.get('message_text', [''])[0]

    if not fullname or not message_text:
        return 400, "text/html; charset=utf-8", "نام و متن پیام الزامی است."

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO messages (fullname, email, phone, topic, message_text) VALUES (?,?,?,?,?)",
            (fullname, email, phone, topic, message_text)
        )
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "پیام با موفقیت ثبت شد. <a href='/contact'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"خطا: {e}"

def handle_register(params):
    first_name = params.get('first_name', [''])[0]
    last_name = params.get('last_name', [''])[0]
    phone = params.get('phone', [''])[0]
    password = params.get('password', [''])[0]
    confirm_password = params.get('confirm_password', [''])[0]
    account_type = params.get('account_type', [''])[0]

    if not all([first_name, last_name, phone, password, confirm_password, account_type]):
        return 400, "text/html; charset=utf-8", "تمامی فیلدهای الزامی را پر کنید."
    if password != confirm_password:
        return 400, "text/html; charset=utf-8", "رمز عبور و تکرار آن مطابقت ندارند."
    if len(password) < 8:
        return 400, "text/html; charset=utf-8", "رمز عبور باید حداقل ۸ کاراکتر باشد."
    if account_type not in ('guest', 'host'):
        return 400, "text/html; charset=utf-8", "نوع حساب نامعتبر است."

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (first_name, last_name, phone, password_hash, account_type) VALUES (?,?,?,?,?)",
            (first_name, last_name, phone, hash_password(password), account_type)
        )
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "ثبت‌نام با موفقیت انجام شد. <a href='/register'>بازگشت</a>"
    except sqlite3.IntegrityError:
        return 400, "text/html; charset=utf-8", "این شماره موبایل قبلاً ثبت شده است."
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"خطا: {e}"

def handle_add_property(params):
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
        conn.execute(
            """INSERT INTO properties 
               (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (host_id, title, description, property_type, location, float(price_per_night),
             int(max_guests), int(bedrooms), int(bathrooms))
        )
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "اقامتگاه با موفقیت اضافه شد. <a href='/add-property'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"خطا: {e}"


def view_catalog():
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, title, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, description FROM properties"
        ).fetchall()
        conn.close()
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"<p>خطا در واکشی اقامتگاه‌ها: {e}</p>"

    html = generate_catalog_html("کاتالوگ اقامتگاه‌ها", rows)
    return 200, "text/html; charset=utf-8", html

def edit_user_form(user_id):
    try:
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if not user:
            return 404, "text/html; charset=utf-8", "کاربری با این شناسه یافت نشد."
        html = generate_edit_user_form(user)
        return 200, "text/html; charset=utf-8", html
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"<p>خطا: {e}</p>"

def edit_property_form(property_id):
    try:
        conn = get_db()
        prop = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
        conn.close()
        if not prop:
            return 404, "text/html; charset=utf-8", "اقامتگاهی با این شناسه یافت نشد."
        html = generate_edit_property_form(prop)
        return 200, "text/html; charset=utf-8", html
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"<p>خطا: {e}</p>"

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
        conn.execute(
            "UPDATE users SET first_name=?, last_name=?, phone=?, account_type=? WHERE id=?",
            (first_name, last_name, phone, account_type, user_id)
        )
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "کاربر با موفقیت ویرایش شد. <a href='/admin/users'>بازگشت به لیست</a>"
    except sqlite3.IntegrityError:
        return 400, "text/html; charset=utf-8", "این شماره موبایل قبلاً ثبت شده است."
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"خطا: {e}"

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
        conn.execute(
            """UPDATE properties 
               SET title=?, description=?, property_type=?, location=?, price_per_night=?, max_guests=?, bedrooms=?, bathrooms=?
               WHERE id=?""",
            (title, description, property_type, location, float(price_per_night),
             int(max_guests), int(bedrooms), int(bathrooms), property_id)
        )
        conn.commit()
        conn.close()
        return 200, "text/html; charset=utf-8", "اقامتگاه با موفقیت ویرایش شد. <a href='/admin/properties'>بازگشت به لیست</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", f"خطا: {e}"


def view_home():
    try:
        conn = get_db()
        # واکشی 6 اقامتگاه آخر به عنوان محبوب‌ها (می‌توان معیار دیگری گذاشت)
        rows = conn.execute(
            "SELECT id, title, property_type, location, price_per_night FROM properties ORDER BY id DESC LIMIT 6"
        ).fetchall()
        conn.close()
    except Exception as e:
        rows = []
    html = generate_home_html(rows)
    return 200, "text/html; charset=utf-8", html