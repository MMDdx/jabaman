# controllers/property_controller.py
"""کنترلر اقامتگاه — افزودن اقامتگاه توسط میزبان + حذف تصویر.

مسیرهای تحت پوشش:
- POST /add-property                                   → افزودن اقامتگاه جدید
- POST /property/<int:property_id>/images/<int:image_id>/delete   → حذف تصویر

نکته: ویرایش و حذف اقامتگاه در admin_controller.py است چون فقط ادمین دسترسی دارد.
"""
import models
from views import generate_error_page

from ._shared import (
    Response,
    require_login,
    require_admin,
    allowed_image_filename,
    save_uploaded_image,
    delete_image_file,
    MAX_IMAGE_SIZE,
    get_text_field,
)


def handle_add_property(params, user_id, wants_json=False):
    """افزودن اقامتگاه جدید — host_id از نشست گرفته می‌شود.

    فیلد اختیاری extra_guest_charge نیز از فرم خوانده می‌شود. اگر
    وارد نشده بود، از DEFAULT_EXTRA_GUEST_CHARGE_PER_PERSON_PER_NIGHT
    استفاده می‌شود.

    این هندلر همچنین تصاویر آپلودی را (تا MAX_PROPERTY_IMAGES عدد) در فیلد
    "images" دریافت و ذخیره می‌کند.
    """
    if not require_login(user_id):
        return Response.login_required()

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
    image_files = params.get('images', [])  # لیست فایل‌های آپلودی

    def fail(msg, status=400):
        if wants_json:
            return Response.json(status, {"success": False, "error": msg})
        return Response.html(status, msg + " <a href='/add-property'>بازگشت</a>")

    if not all([title, property_type, location, price_per_night, max_guests]):
        return fail("فیلدهای الزامی را پر کنید.")

    try:
        # جمع‌آوری امکانات به‌صورت لیست کاما جدا
        amenities = ",".join(amenities_list) if amenities_list else None

        # اعتبارسنجی extra_guest_charge اگر وارد شده باشد
        egc = None
        if extra_guest_charge_raw is not None and extra_guest_charge_raw != '':
            try:
                egc = float(extra_guest_charge_raw)
                if egc < 0:
                    return fail("هزینه‌ی مهمان اضافی نمی‌تواند منفی باشد.")
            except (ValueError, TypeError):
                return fail("فرمت هزینه‌ی مهمان اضافی نامعتبر است.")

        property_id = models.create_property(
            user_id,  # ← host_id از نشست
            title, description, property_type, location,
            float(price_per_night), int(max_guests),
            int(bedrooms), int(bathrooms),
            amenities=amenities,
            extra_guest_charge=egc
        )

        # ذخیره‌ی تصاویر آپلودی (تا MAX_PROPERTY_IMAGES)
        if property_id and image_files:
            saved_count = 0
            for f in image_files:
                if saved_count >= models.MAX_PROPERTY_IMAGES:
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
                if saved_path:
                    if models.add_property_image(property_id, saved_path):
                        saved_count += 1

        if wants_json:
            return Response.json(200, {"success": True, "redirect": "/catalog"})
        return Response.redirect("/catalog")
    except ValueError as e:
        return fail(f"ورودی نامعتبر: {e}")
    except Exception as e:
        if wants_json:
            return Response.json(500, {"success": False, "error": str(e)})
        return Response.html(500, generate_error_page(500, str(e)))


def handle_delete_property_image(property_id, image_id, user_id):
    """حذف یک تصویر از اقامتگاه.

    فقط ادمین یا میزبان مالک اقامتگاه می‌تواند این کار را انجام دهد.
    فایل فیزیکی روی دیسک هم حذف می‌شود.
    """
    if not require_login(user_id):
        return Response.login_required()

    if not property_id or not image_id:
        return Response.html(400, generate_error_page(400, "شناسه نامعتبر", user_id))

    # بررسی مالکیت یا ادمین بودن
    is_admin = require_admin(user_id)
    if not is_admin:
        # اگر ادمین نیست، باید میزبان مالک باشد
        prop = models.get_property(property_id)
        if not prop or prop.get("host_id") != user_id:
            return Response.forbidden(user_id)

    # بررسی اینکه تصویر واقعاً متعلق به این اقامتگاه است
    img = models.get_image_by_id(image_id)
    if not img or img.get("property_id") != property_id:
        return Response.html(404, generate_error_page(404, "تصویر یافت نشد", user_id))

    # حذف از دیتابیس (مسیر فایل برمی‌گردد)
    file_path = models.delete_property_image(image_id)
    # حذف فایل فیزیکی
    if file_path:
        delete_image_file(file_path)

    # ریدایرکت به صفحه‌ی ویرایش اقامتگاه (ادمین) یا جزئیات
    if is_admin:
        return Response.redirect(f"/admin/properties/{property_id}/edit")
    return Response.redirect(f"/property/{property_id}")
