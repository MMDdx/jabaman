
from template_engine import render_template

def generate_home_html(featured_properties):
    props = []
    icon_map = {
        "villa": "🏡",
        "apartment": "🏢",
        "cottage": "🛖",
        "villa-garden": "🌳",
        "penthouse": "🏙️",
        "other": "🏠"
    }
    for p in featured_properties:
        props.append({
            "id": p["id"],
            "title": p["title"],
            "location": p["location"],
            "price_per_night": f"{p['price_per_night']:,.0f}",
            "type_icon": icon_map.get(p["property_type"], "🏠")
        })
    return render_template("home.html", {"properties": props})

def generate_catalog_html(title, properties):
    props = []
    icon_map = {
        "villa": "🏡", "apartment": "🏢", "cottage": "🛖",
        "villa-garden": "🌳", "penthouse": "🏙️", "other": "🏠"
    }
    for p in properties:
        desc = p["description"] or ""      # ← اصلاح شد
        props.append({
            "id": p["id"],
            "title": p["title"],
            "location": p["location"],
            "price_per_night": f"{p['price_per_night']:,.0f}",
            "max_guests": p["max_guests"],
            "bedrooms": p["bedrooms"] or 0,     # ← اگر NULL نباشد
            "bathrooms": p["bathrooms"] or 0,
            "short_desc": desc[:100] + "..." if len(desc) > 100 else desc,
            "type_icon": icon_map.get(p["property_type"], "🏠")
        })
    return render_template("catalog.html", {"title": title, "properties": props})

def generate_table_html(title, columns, rows):
    return render_template("table.html", {"title": title, "columns": columns, "rows": rows})

def generate_edit_user_form(user):
    return render_template("edit_user.html", {"user": user})

def generate_edit_property_form(property_data):
    return render_template("edit_property.html", {"property": property_data})

def generate_property_detail(prop, comments):
    # فرمت قیمت
    prop = dict(prop)
    prop["price_per_night"] = f"{prop['price_per_night']:,.0f}"
    return render_template("property_detail.html", {"property": prop, "comments": comments})

def generate_cart_page(cart_items):
    items = []
    total = 0
    for item in cart_items:
        items.append({
            "title": item["title"],
            "location": item["location"],
            "price_per_night": f"{item['price_per_night']:,.0f}"
        })
        total += item["price_per_night"]
    return render_template("cart.html", {"items": items, "total": f"{total:,.0f}"})

def generate_wishlist_page(wishlist_items):
    items = []
    for item in wishlist_items:
        img = (item.get('images') or "").split(",")[0].strip()
        items.append({
            "id": item["id"],
            "title": item["title"],
            "location": item["location"],
            "price_per_night": f"{item['price_per_night']:,.0f}",
            "image_url": img
        })
    return render_template("wishlist.html", {"items": items})

def generate_message_detail(message_data):
    msg = dict(message_data)
    msg["read_status"] = "خوانده شده" if msg.get("is_read") else "خوانده نشده"
    return render_template("message_detail.html", {"message": msg})

def generate_error_page(status_code, message=""):
    if status_code == 404:
        title = "صفحه پیدا نشد"
        desc = "متأسفانه صفحه‌ای که به دنبال آن هستید وجود ندارد یا حذف شده است."
    elif status_code == 403:
        title = "دسترسی غیرمجاز"
        desc = "شما مجوز مشاهده این صفحه را ندارید."
    elif status_code == 500:
        title = "خطای سرور"
        desc = "مشکلی در سرور رخ داده است. لطفاً بعداً تلاش کنید."
    else:
        title = "خطا"
        desc = message or "خطایی رخ داده است."
    return render_template("error.html", {"code": status_code, "title": title, "description": desc})
