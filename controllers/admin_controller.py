# controllers/admin_controller.py
"""کنترلر پنل ادمین — همه‌ی مسیرهای /admin/*.

مسیرهای تحت پوشش:

GET:
- /admin                                → داشبورد
- /admin/users                          → لیست کاربران
- /admin/messages                       → لیست پیام‌ها
- /admin/properties                     → لیست اقامتگاه‌ها
- /admin/comments                       → لیست نظرات
- /admin/reservations                   → لیست رزروها
- /admin/users/<id>/edit                → فرم ویرایش کاربر
- /admin/properties/<id>/edit           → فرم ویرایش اقامتگاه
- /admin/properties/<id>/delete         → حذف اقامتگاه
- /admin/users/<id>/delete              → حذف کاربر
- /admin/messages/<id>/delete           → حذف پیام
- /admin/comments/<id>/delete           → حذف نظر
- /admin/reservations/<id>/cancel       → لغو رزرو توسط ادمین

POST:
- /admin/users/<id>/edit                → ذخیره ویرایش کاربر
- /admin/properties/<id>/edit           → ذخیره ویرایش اقامتگاه
"""
import sqlite3

import models
from utils.security import hash_password  # noqa: F401  (ممکن است در آینده استفاده شود)
from views import (
    generate_admin_dashboard,
    generate_table_html,
    generate_edit_user_form,
    generate_edit_property_form,
    generate_error_page,
)

from ._shared import (
    Response,
    require_admin,
    require_login,
    EMAIL_REGEX,
    allowed_image_filename,
    save_uploaded_image,
    delete_image_file,
    MAX_IMAGE_SIZE,
    get_text_field,
)


# ========================
#  GET — داشبورد و لیست‌ها
# ========================
def dashboard(user_id):
    """داشبورد ادمین — آمار کلی + آخرین پیام‌ها و نظرات."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    stats = models.get_admin_stats()
    recent_messages = models.get_all_messages()[:5]
    recent_comments = models.get_all_comments()[:5]
    return Response.html(200, generate_admin_dashboard(
        stats, recent_messages, recent_comments, user_id
    ))


def list_users(user_id):
    """لیست همه‌ی کاربران در جدول ادمین."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    users = models.get_all_users()
    formatted = []
    for u in users:
        row = dict(u)
        row["شناسه"] = u.get("id")
        row["نام"] = u.get("first_name")
        row["نام خانوادگی"] = u.get("last_name")
        row["ایمیل"] = u.get("email")
        row["موبایل"] = u.get("phone") or "—"
        row["نوع حساب"] = "میزبان" if u.get("account_type") == "host" else "مهمان"
        row["ادمین"] = "بله" if u.get("is_admin") else "—"
        row["تاریخ ثبت‌نام"] = u.get("created_at")
        formatted.append(row)
    return Response.html(200, generate_table_html(
        "کاربران",
        ["شناسه", "نام", "نام خانوادگی", "ایمیل", "موبایل", "نوع حساب", "ادمین", "تاریخ ثبت‌نام"],
        formatted, user_id
    ))


def list_messages(user_id):
    """لیست همه‌ی پیام‌های تماس با ما."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    messages = models.get_all_messages()
    formatted = []
    for m in messages:
        row = dict(m)
        row["شناسه"] = m.get("id")
        row["فرستنده"] = m.get("fullname")
        row["ایمیل"] = m.get("email") or "—"
        row["تلفن"] = m.get("phone") or "—"
        row["موضوع"] = m.get("topic") or "—"
        # متن کامل پیام در صفحه‌ی جزئیات است؛ اینجا فقط پیش‌نمایش کوتاه
        text = m.get("message_text") or ""
        row["متن"] = (text[:60] + "…") if len(text) > 60 else text
        row["خوانده‌شده"] = "✓ بله" if m.get("is_read") else "✗ خیر"
        row["تاریخ"] = m.get("created_at")
        formatted.append(row)
    return Response.html(200, generate_table_html(
        "پیام‌ها",
        ["شناسه", "فرستنده", "ایمیل", "تلفن", "موضوع", "متن", "خوانده‌شده", "تاریخ"],
        formatted, user_id
    ))


def list_properties(user_id):
    """لیست همه‌ی اقامتگاه‌ها."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    properties = models.get_all_properties()
    formatted = []
    for p in properties:
        row = dict(p)
        row["شناسه"] = p.get("id")
        row["میزبان"] = p.get("host_id")
        row["عنوان"] = p.get("title")
        row["نوع"] = p.get("property_type")
        row["موقعیت"] = p.get("location")
        row["قیمت/شب"] = f"{float(p.get('price_per_night') or 0):,.0f}"
        row["ظرفیت"] = p.get("max_guests")
        row["اتاق"] = p.get("bedrooms")
        row["سرویس"] = p.get("bathrooms")
        row["تاریخ ثبت"] = p.get("created_at")
        formatted.append(row)
    return Response.html(200, generate_table_html(
        "اقامتگاه‌ها",
        ["شناسه", "میزبان", "عنوان", "نوع", "موقعیت", "قیمت/شب", "ظرفیت", "اتاق", "سرویس", "تاریخ ثبت"],
        formatted, user_id
    ))


def list_comments(user_id):
    """لیست همه‌ی نظرات."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    comments = models.get_all_comments()
    formatted = []
    for c in comments:
        row = dict(c)
        row["شناسه"] = c.get("id")
        row["کاربر"] = c.get("user_name")
        row["اقامتگاه"] = c.get("property_title")
        row["متن نظر"] = c.get("comment_text")
        row["امتیاز"] = f"{c.get('rating', 0)} ★"
        row["تاریخ"] = c.get("created_at")
        formatted.append(row)
    return Response.html(200, generate_table_html(
        "نظرات",
        ["شناسه", "کاربر", "اقامتگاه", "متن نظر", "امتیاز", "تاریخ"],
        formatted, user_id
    ))


def list_reservations(user_id):
    """لیست همه‌ی رزروها با ترجمه‌ی وضعیت به فارسی."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    reservations = models.get_all_reservations()
    status_fa_map = {
        "confirmed": "تایید شده",
        "cancelled": "لغو شده",
        "completed": "تکمیل شده",
    }
    formatted = []
    for r in reservations:
        row = dict(r)
        row["شناسه"] = r.get("id")
        row["کد رزرو"] = r.get("reservation_code") or "—"
        row["کاربر"] = r.get("user_name") or "—"
        row["اقامتگاه"] = r.get("property_title") or "—"
        row["ورود"] = r.get("check_in_date") or "—"
        row["خروج"] = r.get("check_out_date") or "—"
        row["شب"] = r.get("nights") or 1
        row["مهمان"] = f"{r.get('guests') or 1}" + (
            f" (+{r.get('extra_guests')})" if r.get("extra_guests") else ""
        )
        try:
            row["مبلغ"] = f"{float(r.get('total_price') or 0):,.0f}"
        except (TypeError, ValueError):
            row["مبلغ"] = "0"
        status_en = r.get("status") or "confirmed"
        row["وضعیت"] = status_fa_map.get(status_en, status_en)
        row["status"] = status_en
        row["تاریخ ثبت"] = r.get("created_at")
        formatted.append(row)
    return Response.html(200, generate_table_html(
        "رزروها",
        ["شناسه", "کد رزرو", "کاربر", "اقامتگاه", "ورود", "خروج", "شب", "مهمان", "مبلغ", "وضعیت", "تاریخ ثبت"],
        formatted, user_id
    ))


# ========================
#  GET — فرم‌های ویرایش
# ========================
def edit_user_form(user_id_target, user_id):
    """نمایش فرم ویرایش یک کاربر."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    user = models.get_user(user_id_target)
    if not user:
        return Response.html(404, generate_error_page(404, user_id=user_id))
    return Response.html(200, generate_edit_user_form(user, user_id))


def edit_property_form(property_id, user_id):
    """نمایش فرم ویرایش یک اقامتگاه."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    prop = models.get_property(property_id)
    if not prop:
        return Response.html(404, generate_error_page(404, user_id=user_id))
    return Response.html(200, generate_edit_property_form(prop, user_id))


# ========================
#  GET — حذف
# ========================
def delete_property(property_id, user_id):
    """حذف اقامتگاه — ابتدا تصاویر فیزیکی، سپس رکورد دیتابیس."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    # گرفتن مسیرهای فایل قبل از حذف از DB
    image_paths = []
    try:
        for img in models.get_property_images(property_id):
            image_paths.append(img.get('image_path'))
    except Exception:
        pass
    models.delete_property(property_id)
    # حذف فایل‌های فیزیکی پس از حذف موفق از DB
    for p in image_paths:
        delete_image_file(p)
    return Response.redirect("/admin/properties")


def delete_user(user_id_target, user_id):
    """حذف کاربر — جلوگیری از حذف خود کاربر فعلی."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    if user_id_target == user_id:
        return Response.html(400, "نمی‌توانید حساب خودتان را حذف کنید. "
                                  "<a href='/admin/users'>بازگشت</a>")
    models.delete_user(user_id_target)
    return Response.redirect("/admin/users")


def delete_message(message_id, user_id):
    """حذف پیام تماس."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    models.delete_message(message_id)
    return Response.redirect("/admin/messages")


def delete_comment(comment_id, user_id):
    """حذف نظر."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    models.delete_comment(comment_id)
    return Response.redirect("/admin/comments")


def cancel_reservation(reservation_id, user_id):
    """لغو رزرو توسط ادمین."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)
    ok, err = models.cancel_reservation(reservation_id, is_admin=True)
    if not ok:
        return Response.html(400, generate_error_page(400, err, user_id))
    return Response.redirect("/admin/reservations")


# ========================
#  POST — ذخیره ویرایش
# ========================
def handle_edit_user(params, user_id_target, user_id):
    """ذخیره‌ی ویرایش کاربر."""
    if not require_admin(user_id):
        return Response.forbidden(user_id)

    first_name = params.get('first_name', [''])[0].strip()
    last_name = params.get('last_name', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    account_type = params.get('account_type', [''])[0]

    if not all([first_name, last_name, email, account_type]):
        return Response.html(400, "فیلدهای الزامی را پر کنید.")
    if not EMAIL_REGEX.match(email):
        return Response.html(400, "ایمیل نامعتبر است.")
    if account_type not in ('guest', 'host'):
        return Response.html(400, "نوع حساب نامعتبر است.")

    try:
        models.update_user(user_id_target, first_name, last_name, email, account_type, phone=phone or None)
        return Response.redirect("/admin/users")
    except sqlite3.IntegrityError:
        return Response.html(400, "این ایمیل قبلاً ثبت شده است.")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def handle_edit_property(params, property_id, user_id):
    """ذخیره‌ی ویرایش اقامتگاه — شامل تصاویر جدید آپلودی.

    فیلد اختیاری extra_guest_charge نیز از فرم خوانده می‌شود.
    """
    if not require_admin(user_id):
        return Response.forbidden(user_id)

    title = get_text_field(params, 'title')
    description = get_text_field(params, 'description')
    property_type = get_text_field(params, 'property_type')
    location = get_text_field(params, 'location')
    price_per_night = get_text_field(params, 'price_per_night', '0') or '0'
    max_guests = get_text_field(params, 'max_guests', '1') or '1'
    bedrooms = get_text_field(params, 'bedrooms', '0') or '0'
    bathrooms = get_text_field(params, 'bathrooms', '0') or '0'
    amenities_list = [v for v in params.get('amenities', []) if isinstance(v, str)]
    extra_guest_charge_raw = get_text_field(params, 'extra_guest_charge', None)
    image_files = params.get('images', [])  # لیست فایل‌های آپلودی جدید

    if not all([title, property_type, location, price_per_night, max_guests]):
        return Response.html(400, "فیلدهای الزامی را پر کنید.")

    try:
        amenities = ",".join(amenities_list) if amenities_list else None
        # اعتبارسنجی extra_guest_charge
        egc = None
        if extra_guest_charge_raw is not None and extra_guest_charge_raw != '':
            try:
                egc = float(extra_guest_charge_raw)
                if egc < 0:
                    return Response.html(400, "هزینه‌ی مهمان اضافی نمی‌تواند منفی باشد.")
            except (ValueError, TypeError):
                return Response.html(400, "فرمت هزینه‌ی مهمان اضافی نامعتبر است.")

        models.update_property(
            property_id, title, description, property_type, location,
            float(price_per_night), int(max_guests),
            int(bedrooms), int(bathrooms),
            amenities=amenities,
            extra_guest_charge=egc
        )

        # افزودن تصاویر جدید (تا سقف MAX_PROPERTY_IMAGES)
        if image_files:
            current_count = models.count_property_images(property_id)
            for f in image_files:
                if current_count >= models.MAX_PROPERTY_IMAGES:
                    break
                if not isinstance(f, dict) or not f.get('filename'):
                    continue
                if not f.get('data'):
                    continue
                if not allowed_image_filename(f.get('filename')):
                    continue
                if len(f['data']) > MAX_IMAGE_SIZE:
                    continue
                saved_path = save_uploaded_image(f, property_id)
                if saved_path and models.add_property_image(property_id, saved_path):
                    current_count += 1

        return Response.redirect("/admin/properties")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))
