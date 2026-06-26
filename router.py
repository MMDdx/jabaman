import sqlite3
import urllib.parse
from hashlib import sha256
import models
from views import (
    generate_home_html, generate_catalog_html, generate_table_html,
    generate_edit_user_form, generate_edit_property_form,
    generate_error_page,
    generate_property_detail, generate_cart_page, generate_wishlist_page, generate_message_detail
)

CURRENT_USER_ID = 1  # کاربر پیش‌فرض (تا زمان پیاده‌سازی نشست)

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def match_route(path, pattern):
    path_parts = path.strip('/').split('/')
    pattern_parts = pattern.strip('/').split('/')
    if len(path_parts) != len(pattern_parts):
        return None
    params = {}
    for pp, pat in zip(path_parts, pattern_parts):
        if pat.startswith('<') and pat.endswith('>'):
            param_type = pat[1:-1].split(':')[0]
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

# ========================
#         GET
# ========================
def process_get(path):
    path = path.split('?')[0]

    if path == "/" or path == "":
        featured = models.get_featured_properties()
        return 200, "text/html; charset=utf-8", generate_home_html(featured)

    if path == "/catalog":
        properties = models.get_all_properties()
        return 200, "text/html; charset=utf-8", generate_catalog_html("کاتالوگ اقامتگاه‌ها", properties)

    if path == "/cart":
        items = models.get_cart_items(CURRENT_USER_ID)
        return 200, "text/html; charset=utf-8", generate_cart_page(items)

    if path == "/wishlist":
        items = models.get_wishlist_items(CURRENT_USER_ID)
        return 200, "text/html; charset=utf-8", generate_wishlist_page(items)

    if path == "/admin/users":
        users = models.get_all_users()
        return 200, "text/html; charset=utf-8", generate_table_html("کاربران", ["شناسه", "نام", "نام خانوادگی", "موبایل", "نوع حساب", "تاریخ ثبت‌نام"], users)

    if path == "/admin/messages":
        messages = models.get_all_messages()
        return 200, "text/html; charset=utf-8", generate_table_html("پیام‌ها", ["شناسه", "فرستنده", "ایمیل", "تلفن", "موضوع", "متن", "خوانده‌شده", "تاریخ"], messages)

    if path == "/admin/properties":
        properties = models.get_all_properties()
        return 200, "text/html; charset=utf-8", generate_table_html("اقامتگاه‌ها", ["شناسه", "میزبان", "عنوان", "نوع", "موقعیت", "قیمت/شب", "ظرفیت", "اتاق", "سرویس", "تاریخ ثبت"], properties)

    # ---------- Dynamic routes ----------
    params = match_route(path, "/property/<int:id>")
    if params:
        prop = models.get_property(params['id'])
        if not prop:
            return 404, "text/html; charset=utf-8", generate_error_page(404)
        comments = models.get_comments_for_property(params['id'])
        return 200, "text/html; charset=utf-8", generate_property_detail(prop, comments)

    params = match_route(path, "/message/<int:id>")
    if params:
        msg = models.get_message(params['id'])
        if not msg:
            return 404, "text/html; charset=utf-8", generate_error_page(404)
        return 200, "text/html; charset=utf-8", generate_message_detail(msg)

    params = match_route(path, "/admin/users/<int:id>/edit")
    if params:
        user = models.get_user(params['id'])
        if not user:
            return 404, "text/html; charset=utf-8", generate_error_page(404)
        return 200, "text/html; charset=utf-8", generate_edit_user_form(user)

    params = match_route(path, "/admin/properties/<int:id>/edit")
    if params:
        prop = models.get_property(params['id'])
        if not prop:
            return 404, "text/html; charset=utf-8", generate_error_page(404)
        return 200, "text/html; charset=utf-8", generate_edit_property_form(prop)

    return None

# ========================
#         POST
# ========================
def process_post(path, body):
    path = path.split('?')[0]
    params = urllib.parse.parse_qs(body.decode()) if body else {}

    if path == "/contact":
        return handle_contact(params)
    if path == "/register":
        return handle_register(params)
    if path == "/add-property":
        return handle_add_property(params)
    if path == "/cart/add":
        return handle_add_to_cart(params)
    if path == "/wishlist/add":
        return handle_add_to_wishlist(params)
    if path == "/comment/add":
        return handle_add_comment(params)

    p = match_route(path, "/admin/users/<int:id>/edit")
    if p:
        return handle_edit_user(params, p['id'])

    p = match_route(path, "/admin/properties/<int:id>/edit")
    if p:
        return handle_edit_property(params, p['id'])

    return 404, "text/html; charset=utf-8", generate_error_page(404)

# ---------- handler functions ----------
def handle_contact(params):
    fullname = params.get('fullname', [''])[0]
    email = params.get('email', [''])[0]
    phone = params.get('phone', [''])[0]
    topic = params.get('topic', [''])[0]
    message_text = params.get('message_text', [''])[0]
    if not fullname or not message_text:
        return 400, "text/html; charset=utf-8", "نام و متن پیام الزامی است."
    try:
        models.create_message(fullname, email, phone, topic, message_text)
        return 200, "text/html; charset=utf-8", "پیام با موفقیت ثبت شد. <a href='/contact'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

def handle_register(params):
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
        models.create_user(first_name, last_name, phone, hash_password(password), account_type)
        return 200, "text/html; charset=utf-8", "ثبت‌نام با موفقیت انجام شد. <a href='/register'>بازگشت</a>"
    except sqlite3.IntegrityError:
        return 400, "text/html; charset=utf-8", "این شماره موبایل قبلاً ثبت شده است."
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

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
        models.create_property(
            host_id, title, description, property_type, location,
            float(price_per_night), int(max_guests), int(bedrooms), int(bathrooms)
        )
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
        models.update_user(user_id, first_name, last_name, phone, account_type)
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
        models.update_property(
            property_id, title, description, property_type, location,
            float(price_per_night), int(max_guests), int(bedrooms), int(bathrooms)
        )
        return 200, "text/html; charset=utf-8", "اقامتگاه با موفقیت ویرایش شد. <a href='/admin/properties'>بازگشت</a>"
    except Exception as e:
        return 500, "text/html; charset=utf-8", generate_error_page(500, str(e))

def handle_add_to_cart(params):
    property_id = params.get('property_id', [None])[0]
    if not property_id:
        return 400, "text/plain", "شناسه اقامتگاه الزامی است"
    models.add_to_cart(CURRENT_USER_ID, property_id)
    return 303, "text/html", '<meta http-equiv="refresh" content="0;url=/cart">'

def handle_add_to_wishlist(params):
    property_id = params.get('property_id', [None])[0]
    if not property_id:
        return 400, "text/plain", "شناسه اقامتگاه الزامی است"
    models.add_to_wishlist(CURRENT_USER_ID, property_id)
    return 303, "text/html", '<meta http-equiv="refresh" content="0;url=/wishlist">'

def handle_add_comment(params):
    property_id = params.get('property_id', [None])[0]
    comment_text = params.get('comment_text', [''])[0]
    rating = params.get('rating', ['5'])[0]
    if not property_id or not comment_text:
        return 400, "text/plain", "شناسه و متن نظر الزامی است"
    models.add_comment(CURRENT_USER_ID, property_id, comment_text, int(rating))
    return 303, "text/html", f'<meta http-equiv="refresh" content="0;url=/property/{property_id}">'

def error_404():
    return 404, "text/html; charset=utf-8", generate_error_page(404)

def error_403():
    return 403, "text/html; charset=utf-8", generate_error_page(403)

def error_500():
    return 500, "text/html; charset=utf-8", generate_error_page(500)