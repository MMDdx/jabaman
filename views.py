# views.py
"""لایه‌ی View در معماری MVC — تولید HTML با استفاده از template engine.

تغییرات نسخه‌ی فعلی:
- تمام توابع user_id را دریافت و به template می‌فرستند تا navbar یکپارچه باشد.
- صفحات contact / login / signup / add-property از static به templates منتقل شدند
  و حالا از طریق این لایه با user_id رندر می‌شوند.
- logout و login-redirect هم قالب اختصاصی گرفتند تا JS بیرون فایل باشد.
- price formatting یکپارچه.
- is_host نیز به همه‌ی قالب‌ها پاس داده می‌شود تا navbar بتواند دکمه‌ی
  «افزودن اقامتگاه» را فقط برای میزبان‌ها (نه مهمان‌ها) نمایش دهد.
"""
import models
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


def _is_host(user_id):
    """بررسی میزبان بودن کاربر. در صورت عدم ورود، False برمی‌گرداند.

    کاربرد: کنترل نمایش دکمه‌ی «افزودن اقامتگاه» در navbar.
    """
    if not user_id:
        return False
    return models.is_host(user_id)


def _is_admin(user_id):
    """بررسی ادمین بودن کاربر. در صورت عدم ورود، False برمی‌گرداند.

    کاربرد: کنترل نمایش دکمه‌ی «پنل مدیریت» در navbar صفحات عمومی.
    """
    if not user_id:
        return False
    return models.is_admin(user_id)


def _base_context(user_id):
    """ساخت context پایه با user_id، is_host و is_admin برای استفاده در همه‌ی قالب‌ها."""
    return {
        "user_id": user_id,
        "is_host": _is_host(user_id),
        "is_admin": _is_admin(user_id),
    }


# ========================
#   صفحات اصلی (عمومی)
# ========================

def generate_home_html(featured_properties, user_id=None):
    # گرفتن تصویر شاخص برای همه‌ی اقامتگاه‌ها در یک کوئری
    pids = [p["id"] for p in featured_properties if p.get("id")]
    featured_imgs = {}
    try:
        featured_imgs = models.get_featured_images_for_properties(pids)
    except Exception:
        pass

    props = []
    for p in featured_properties:
        props.append({
            "id": p["id"],
            "title": p["title"],
            "location": p["location"],
            "price_per_night": _fmt_price(p["price_per_night"]),
            "type_icon": ICON_MAP.get(p.get("property_type"), "🏠"),
            "image_url": featured_imgs.get(p["id"], "")
        })
    ctx = _base_context(user_id)
    ctx["properties"] = props
    return render_template("home.html", ctx)


def generate_catalog_html(title, properties, user_id=None):
    # گرفتن تصویر شاخص برای همه‌ی اقامتگاه‌ها در یک کوئری
    pids = [p["id"] for p in properties if p.get("id")]
    featured_imgs = {}
    try:
        featured_imgs = models.get_featured_images_for_properties(pids)
    except Exception:
        pass

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
            "type_icon": ICON_MAP.get(p.get("property_type"), "🏠"),
            "image_url": featured_imgs.get(p["id"], "")
        })
    ctx = _base_context(user_id)
    ctx["title"] = title
    ctx["properties"] = props
    return render_template("catalog.html", ctx)


def generate_property_detail(prop, comments, user_id=None):
    """prop و comments باید dict باشند.

    نکته: در نسخه‌ی جدید، اقامتگاه به‌جای یک فلگ is_reserved کلی، بر اساس
    بازه‌های تاریخی رزرو می‌شود. بنابراین badge «رزرو شده» حذف شده و به‌جای
    آن، لیست تاریخ‌های رزروشده به کاربر نمایش داده می‌شود تا بداند کدام
    بازه‌ها قابل انتخاب نیستند.
    """
    if hasattr(prop, "keys"):
        prop = dict(prop)
    prop["price_per_night_fmt"] = _fmt_price(prop.get("price_per_night"))
    # is_reserved فقط یک علامت سریع است که «حداقل یک رزرو فعال» دارد.
    # این مقدار دیگر برای تصمیم نهایی استفاده نمی‌شود.
    prop["is_reserved"] = bool(prop.get("is_reserved"))
    # محاسبه‌ی حداکثر مهمان مجاز (۳ برابر ظرفیت استاندارد)
    try:
        mg = int(prop.get("max_guests") or 1)
    except (TypeError, ValueError):
        mg = 1
    prop["max_guests_x3"] = mg * 3
    # هزینه‌ی مهمان اضافی اختصاصی همین اقامتگاه
    # اگر مقدار نبود، از پیش‌فرض سراسری استفاده می‌کنیم
    try:
        egc = float(prop.get("extra_guest_charge")
                    or models.DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    except (TypeError, ValueError):
        egc = float(models.DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT)
    prop["extra_guest_charge"] = egc
    prop["extra_guest_charge_fmt"] = _fmt_price(egc)
    # گرفتن رزروهای آینده‌ی این اقامتگاه برای نمایش در صفحه
    upcoming_reservations = []
    try:
        upcoming_reservations = models.get_reservations_for_property(prop.get("id"))
    except Exception:
        pass
    # گرفتن لیست تصاویر اقامتگاه (تا ۳ تصویر)
    property_images = []
    try:
        property_images = models.get_property_images(prop.get("id"))
    except Exception:
        pass
    # نرمال‌سازی comments
    norm_comments = []
    for c in comments:
        if hasattr(c, "keys"):
            c = dict(c)
        norm_comments.append(c)
    ctx = _base_context(user_id)
    ctx["property"] = prop
    ctx["comments"] = norm_comments
    ctx["comments_count"] = len(norm_comments)
    ctx["upcoming_reservations"] = upcoming_reservations
    ctx["upcoming_reservations_count"] = len(upcoming_reservations)
    ctx["property_images"] = property_images
    ctx["property_images_count"] = len(property_images)
    # مقدار عددی extra_guest_charge برای استفاده در JavaScript (پیش‌نمایش قیمت)
    ctx["extra_guest_charge"] = egc
    ctx["extra_guest_charge_fmt"] = _fmt_price(egc)
    return render_template("property_detail.html", ctx)


# ========================
#   صفحات فرم (عمومی)
# ========================

def generate_contact_page(user_id=None):
    return render_template("contact.html", _base_context(user_id))


def generate_login_page(user_id=None):
    """صفحه‌ی ورود — اکنون قالب‌محور است."""
    return render_template("login.html", _base_context(user_id))


def generate_signup_page(user_id=None):
    """صفحه‌ی ثبت‌نام — اکنون قالب‌محور است."""
    return render_template("signup.html", _base_context(user_id))


def generate_add_property_page(user_id=None):
    """صفحه‌ی درج اقامتگاه — اکنون قالب‌محور است."""
    return render_template("add-property.html", _base_context(user_id))


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
    """ساخت صفحه‌ی سبد خرید با نمایش تاریخ‌ها، تعداد مهمان و قیمت محاسبه‌شده.
    """
    items = []
    grand_total = 0
    has_any_overlap = False
    for item in cart_items:
        total = float(item.get("total_price") or 0)
        grand_total += total
        extra_guests = item.get("extra_guests") or 0
        # has_overlap از models.get_cart_items محاسبه شده است
        has_overlap = bool(item.get("has_overlap"))
        if has_overlap:
            has_any_overlap = True
        items.append({
            "cart_id": item.get("cart_id"),
            "property_id": item.get("property_id"),
            "id": item.get("id"),
            "title": item.get("title"),
            "location": item.get("location"),
            "price_per_night": _fmt_price(item.get("price_per_night")),
            "check_in_date": item.get("check_in_date") or "—",
            "check_out_date": item.get("check_out_date") or "—",
            "guests": item.get("guests") or 1,
            "max_guests": item.get("max_guests"),
            "nights": item.get("nights") or 1,
            "base_price": _fmt_price(item.get("base_price")),
            "extra_guests": extra_guests,
            "has_extra_guests": extra_guests > 0,
            "extra_guest_charge": _fmt_price(item.get("extra_guest_charge")),
            "total_price": _fmt_price(total),
            # هم‌پوشانی با رزروهای تاییدشده‌ی سایر کاربران
            "has_overlap": has_overlap,
            "overlap_message": item.get("overlap_message") or "",
            # is_reserved نگه داشته شده برای backward-compat
            "is_reserved": bool(item.get("is_reserved")),
        })
    ctx = _base_context(user_id)
    ctx["items"] = items
    ctx["total"] = _fmt_price(grand_total)
    ctx["has_any_overlap"] = has_any_overlap
    return render_template("cart.html", ctx)


def generate_checkout_page(cart_items, user_id=None):
    """صفحه‌ی تأیید نهایی خرید — نمایش خلاصه‌ی رزروها و دکمه‌ی تأیید."""
    items = []
    grand_total = 0
    for item in cart_items:
        total = float(item.get("total_price") or 0)
        grand_total += total
        extra_guests = item.get("extra_guests") or 0
        items.append({
            "property_id": item.get("property_id"),
            "title": item.get("title"),
            "location": item.get("location"),
            "check_in_date": item.get("check_in_date") or "—",
            "check_out_date": item.get("check_out_date") or "—",
            "guests": item.get("guests") or 1,
            "nights": item.get("nights") or 1,
            "base_price": _fmt_price(item.get("base_price")),
            "extra_guests": extra_guests,
            "has_extra_guests": extra_guests > 0,
            "extra_guest_charge": _fmt_price(item.get("extra_guest_charge")),
            "total_price": _fmt_price(total),
        })
    ctx = _base_context(user_id)
    ctx["items"] = items
    ctx["total"] = _fmt_price(grand_total)
    ctx["count"] = len(items)
    return render_template("checkout.html", ctx)


def generate_checkout_success_page(reservation_ids, errors, user_id=None):
    """صفحه‌ی موفقیت پس از ایجاد رزرو(ها)."""
    ctx = _base_context(user_id)
    ctx["reservation_ids"] = reservation_ids or []
    ctx["errors"] = errors or []
    ctx["success_count"] = len(reservation_ids or [])
    ctx["has_errors"] = bool(errors)
    return render_template("checkout_success.html", ctx)


def generate_reservations_page(reservations, user_id=None):
    """صفحه‌ی «رزروهای من» — لیست رزروهای کاربر با امکان لغو.
    """
    items = []
    for r in reservations:
        if hasattr(r, "keys"):
            r = dict(r)
        extra_guests = r.get("extra_guests") or 0
        status = r.get("status") or "confirmed"
        items.append({
            "id": r.get("id"),
            "reservation_code": r.get("reservation_code") or f"JAB-{r.get('id'):06d}",
            "property_id": r.get("property_id"),
            "property_title": r.get("property_title") or "—",
            "property_location": r.get("property_location") or "—",
            "check_in_date": r.get("check_in_date") or "—",
            "check_out_date": r.get("check_out_date") or "—",
            "guests": r.get("guests") or 1,
            "extra_guests": extra_guests,
            "has_extra_guests": extra_guests > 0,
            "extra_guest_charge": _fmt_price(r.get("extra_guest_charge")),
            "nights": r.get("nights") or 1,
            "base_price": _fmt_price(r.get("base_price")),
            "total_price": _fmt_price(r.get("total_price")),
            "status": status,
            "status_fa": {
                "confirmed": "تایید شده",
                "cancelled": "لغو شده",
                "completed": "تکمیل شده",
            }.get(status, status),
            "is_confirmed": status == "confirmed",
            "is_cancelled": status == "cancelled",
            "is_completed": status == "completed",
            "created_at": r.get("created_at"),
        })
    ctx = _base_context(user_id)
    ctx["reservations"] = items
    return render_template("reservations.html", ctx)


def generate_wishlist_page(wishlist_items, user_id=None):
    items = []
    for item in wishlist_items:
        # استفاده از جدول جدید property_images برای گرفتن تصویر شاخص
        img = ""
        try:
            img = models.get_featured_image(item["id"])
        except Exception:
            pass
        items.append({
            "wishlist_id": item.get("wishlist_id"),
            "id": item["id"],
            "title": item["title"],
            "location": item["location"],
            "price_per_night": _fmt_price(item["price_per_night"]),
            "image_url": img
        })
    ctx = _base_context(user_id)
    ctx["items"] = items
    return render_template("wishlist.html", ctx)


# ========================
#   صفحات ادمین
# ========================

def generate_admin_dashboard(stats, recent_messages, recent_comments, user_id=None):
    """داشبورد اصلی ادمین — نمایش آمار کلی + آخرین پیام‌ها و نظرات."""
    # پیش‌فرمت‌سازی درآمد کل چون موتور قالب از .format() پشتیبانی نمی‌کند.
    stats = dict(stats) if stats else {}
    try:
        stats["total_revenue_fmt"] = f"{float(stats.get('total_revenue') or 0):,.0f}"
    except (TypeError, ValueError):
        stats["total_revenue_fmt"] = "0"
    ctx = _base_context(user_id)
    ctx["stats"] = stats
    ctx["recent_messages"] = recent_messages or []
    ctx["recent_comments"] = recent_comments or []
    return render_template("admin_dashboard.html", ctx)


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
    ctx = _base_context(user_id)
    ctx["title"] = title
    ctx["columns"] = columns
    ctx["rows"] = norm_rows
    return render_template("table.html", ctx)


def generate_edit_user_form(user, user_id=None):
    """user باید dict باشد."""
    if hasattr(user, "keys"):
        user = dict(user)
    ctx = _base_context(user_id)
    ctx["user"] = user
    return render_template("edit_user.html", ctx)


def generate_edit_property_form(property_data, user_id=None):
    if hasattr(property_data, "keys"):
        property_data = dict(property_data)
    # گرفتن لیست تصاویر فعلی این اقامتگاه
    images = []
    try:
        images = models.get_property_images(property_data.get("id"))
    except Exception:
        pass
    ctx = _base_context(user_id)
    ctx["property"] = property_data
    ctx["property_images"] = images
    ctx["property_images_count"] = len(images)
    ctx["max_images"] = models.MAX_PROPERTY_IMAGES
    ctx["can_add_more_images"] = len(images) < models.MAX_PROPERTY_IMAGES
    ctx["remaining_image_slots"] = max(0, models.MAX_PROPERTY_IMAGES - len(images))
    return render_template("edit_property.html", ctx)


def generate_message_detail(message_data, user_id=None):
    if hasattr(message_data, "keys"):
        message_data = dict(message_data)
    message_data["read_status"] = "خوانده شده" if message_data.get("is_read") else "خوانده نشده"
    ctx = _base_context(user_id)
    ctx["message"] = message_data
    return render_template("message_detail.html", ctx)


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
    ctx = _base_context(user_id)
    ctx["code"] = status_code
    ctx["title"] = title
    ctx["description"] = desc
    return render_template("error.html", ctx)
