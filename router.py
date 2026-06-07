# router.py
import urllib.parse
import sqlite3
from hashlib import sha256
from views import generate_table_html

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
    if path == "/admin/users":
        return view_users()
    elif path == "/admin/messages":
        return view_messages()
    elif path == "/admin/properties":
        return view_properties()
    elif path == "/catalog":
        return view_catalog()
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

    from views import generate_catalog_html  # import در همینجا برای جلوگیری از وابستگی دایره‌ای (اگر نیاز شد)

    html = generate_catalog_html("کاتالوگ اقامتگاه‌ها", rows)
    return 200, "text/html; charset=utf-8", html