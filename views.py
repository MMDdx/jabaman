# views.py
"""لایه‌ی View در معماری MVC — تولید HTML با استفاده از template engine.

تغییرات نسخه‌ی فعلی:
- تمام توابع user_id را دریافت و به template می‌فرستند تا navbar یکپارچه باشد.
- صفحات contact / login / signup / add-property از static به templates منتقل شدند
  و حالا از طریق این لایه با user_id رندر می‌شوند.
- logout و login-redirect هم قالب اختصاصی گرفتند تا JS بیرون فایل باشد.
- price formatting یکپارچه.
"""
from template_engine import render_template

ICON_MAP = {
    "villa": "🏡",
    "apartment": "🏢",
    "cottage": "🛖",
    "villa-garden": "🌳",
    "penthouse": "🏙️",
    "other": "🏠"
}


def _fmt_price(value):
    """فرمت کردن قیمت با جداکننده‌ی هزارگان."""
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "0"


def _get_first_image(images_str):
    """گرفتن اولین تصویر از فیلد images (CSV)."""
    if not images_str:
        return ""
    return images_str.split(",")[0].strip()


# ========================
#   صفحات اصلی (عمومی)
# ========================

def generate_home_html(featured_properties, user_id=None):
    props = []
    for p in featured_properties:
        props.append({
            "id": p["id"],
            "title": p["title"],
            "location": p["location"],
            "price_per_night": _fmt_price(p["price_per_night"]),
            "type_icon": ICON_MAP.get(p.get("property_type"), "🏠")
        })
    return render_template("home.html", {
        "properties": props,
        "user_id": user_id
    })


def generate_catalog_html(title, properties, user_id=None):
    props = []
    for p in properties:
        desc = p.get("description") or ""
        props.append({
            "id": p["id"],
            "title": p["title"],
            "location": p["location"],
            "price_per_night": _fmt_price(p["price_per_night"]),
            "max_guests": p["max_guests"],
            "bedrooms": p.get("bedrooms") or 0,
            "bathrooms": p.get("bathrooms") or 0,
            "short_desc": (desc[:100] + "...") if len(desc) > 100 else desc,
            "type_icon": ICON_MAP.get(p.get("property_type"), "🏠")
        })
    return render_template("catalog.html", {
        "title": title,
        "properties": props,
        "user_id": user_id
    })


def generate_property_detail(prop, comments, user_id=None):
    """prop و comments باید dict باشند."""
    if hasattr(prop, "keys"):
        prop = dict(prop)
    prop["price_per_night_fmt"] = _fmt_price(prop.get("price_per_night"))
    # نرمال‌سازی comments
    norm_comments = []
    for c in comments:
        if hasattr(c, "keys"):
            c = dict(c)
        norm_comments.append(c)
    return render_template("property_detail.html", {
        "property": prop,
        "comments": norm_comments,
        "comments_count": len(norm_comments),
        "user_id": user_id
    })


# ========================
#   صفحات فرم (عمومی)
# ========================

def generate_contact_page(user_id=None):
    """صفحه‌ی تماس با ما — اکنون قالب‌محور است تا navbar یکپارچه باشد."""
    return render_template("contact.html", {"user_id": user_id})


def generate_login_page(user_id=None):
    """صفحه‌ی ورود — اکنون قالب‌محور است."""
    return render_template("login.html", {"user_id": user_id})


def generate_signup_page(user_id=None):
    """صفحه‌ی ثبت‌نام — اکنون قالب‌محور است."""
    return render_template("signup.html", {"user_id": user_id})


def generate_add_property_page(user_id=None):
    """صفحه‌ی درج اقامتگاه — اکنون قالب‌محور است."""
    return render_template("add-property.html", {"user_id": user_id})


def generate_logout_page():
    """صفحه‌ی خروج — JS در فایل جداگانه (logout.js)."""
    return render_template("logout.html", {})


def generate_login_redirect_page():
    """صفحه‌ی «نیاز به ورود» — JS در فایل جداگانه (login_redirect.js)."""
    return render_template("login_redirect.html", {})


# ========================
#   صفحات نیازمند ورود
# ========================

def generate_cart_page(cart_items, user_id=None):
    items = []
    total = 0
    for item in cart_items:
        price = item.get("price_per_night") or 0
        items.append({
            "cart_id": item.get("cart_id"),
            "id": item.get("id"),
            "title": item["title"],
            "location": item["location"],
            "price_per_night": _fmt_price(price)
        })
        total += float(price)
    return render_template("cart.html", {
        "items": items,
        "total": _fmt_price(total),
        "user_id": user_id
    })


def generate_wishlist_page(wishlist_items, user_id=None):
    items = []
    for item in wishlist_items:
        img = _get_first_image(item.get("images"))
        items.append({
            "wishlist_id": item.get("wishlist_id"),
            "id": item["id"],
            "title": item["title"],
            "location": item["location"],
            "price_per_night": _fmt_price(item["price_per_night"]),
            "image_url": img
        })
    return render_template("wishlist.html", {
        "items": items,
        "user_id": user_id
    })


# ========================
#   صفحات ادمین
# ========================

def generate_table_html(title, columns, rows, user_id=None):
    """ساخت جدول ادمین.

    columns: لیست عناوین ستون‌ها
    rows: لیست دیکشنری‌ها. کلیدهای dict باید با keys/columns جدول یکسان باشند.
    """
    # اگر rows از sqlite3.Row باشد، به dict تبدیل کن
    norm_rows = []
    for r in rows:
        if hasattr(r, "keys"):
            r = dict(r)
        norm_rows.append(r)
    return render_template("table.html", {
        "title": title,
        "columns": columns,
        "rows": norm_rows,
        "user_id": user_id
    })


def generate_edit_user_form(user, user_id=None):
    """user باید dict باشد."""
    if hasattr(user, "keys"):
        user = dict(user)
    return render_template("edit_user.html", {
        "user": user,
        "user_id": user_id
    })


def generate_edit_property_form(property_data, user_id=None):
    if hasattr(property_data, "keys"):
        property_data = dict(property_data)
    return render_template("edit_property.html", {
        "property": property_data,
        "user_id": user_id
    })


def generate_message_detail(message_data, user_id=None):
    if hasattr(message_data, "keys"):
        message_data = dict(message_data)
    message_data["read_status"] = "خوانده شده" if message_data.get("is_read") else "خوانده نشده"
    return render_template("message_detail.html", {
        "message": message_data,
        "user_id": user_id
    })


# ========================
#   صفحه خطا
# ========================

def generate_error_page(status_code, message="", user_id=None):
    if status_code == 404:
        title = "صفحه پیدا نشد"
        desc = "متأسفانه صفحه‌ای که به دنبال آن هستید وجود ندارد یا حذف شده است."
    elif status_code == 403:
        title = "دسترسی غیرمجاز"
        desc = "شما مجوز مشاهده این صفحه را ندارید. لطفاً وارد حساب کاربری با دسترسی مناسب شوید."
    elif status_code == 500:
        title = "خطای سرور"
        desc = "مشکلی در سرور رخ داده است. لطفاً بعداً تلاش کنید."
        if message:
            desc += f"<br><small>{message}</small>"
    else:
        title = "خطا"
        desc = message or "خطایی رخ داده است."
    return render_template("error.html", {
        "code": status_code,
        "title": title,
        "description": desc,
        "user_id": user_id
    })