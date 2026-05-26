import urllib.parse
import sqlite3
from hashlib import sha256

DB_NAME = "accommodation.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def process_post(path, body):
    """تنها مسیرهای POST را پردازش می‌کند.
    خروجی: (status, content_type, response_body)
    """
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