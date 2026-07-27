# controllers/cart_controller.py
"""کنترلر سبد خرید — افزودن، حذف، تسویه.

مسیرهای تحت پوشش:
- POST /cart/add                            → افزودن اقامتگاه به سبد
- GET  /cart/<int:id>/remove                → حذف آیتم از سبد
- POST /checkout                            → تسویه و ایجاد رزروها
"""
from datetime import datetime as _dt

import models
from views import (
    generate_error_page,
    generate_checkout_success_page,
)

from ._shared import Response, require_login


def handle_add_to_cart(params, user_id):
    """افزودن اقامتگاه به سبد با تاریخ ورود/خروج و تعداد مهمان.

    فیلدهای مورد انتظار:
    - property_id (الزامی)
    - check_in_date (YYYY-MM-DD)
    - check_out_date (YYYY-MM-DD)
    - guests (عدد)

    اگر بازه‌ی انتخابی با رزروهای تاییدشده‌ی سایر کاربران هم‌پوشانی داشته
    باشد، افزودن به سبد لغو می‌شود و یک پیام خطا نمایش داده می‌شود.
    """
    if not require_login(user_id):
        return Response.login_required()

    property_id = params.get('property_id', [None])[0]
    check_in = params.get('check_in_date', [None])[0]
    check_out = params.get('check_out_date', [None])[0]
    guests = params.get('guests', ['1'])[0]

    if not property_id:
        return Response.html(400, "شناسه اقامتگاه الزامی است")

    # اعتبارسنجی تاریخ‌ها
    try:
        if check_in:
            _dt.strptime(check_in, "%Y-%m-%d")
        if check_out:
            _dt.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return Response.html(400, "فرمت تاریخ نامعتبر است. لطفاً از تقویم استفاده کنید.")

    if check_in and check_out and check_out <= check_in:
        return Response.html(400, "تاریخ خروج باید بعد از تاریخ ورود باشد.")

    try:
        guests_int = int(guests or 1)
        if guests_int < 1:
            guests_int = 1
    except ValueError:
        guests_int = 1

    try:
        success, err = models.add_to_cart(
            user_id, property_id, check_in, check_out, guests_int
        )
        if not success:
            # هم‌پوشانی تاریخ با رزروهای موجود
            return Response.html(400, generate_error_page(
                400,
                "افزودن به سبد خرید ممکن نشد: " + (err or "تداخل تاریخ."),
                user_id
            ))
        return Response.redirect("/cart")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def remove_from_cart(cart_item_id, user_id):
    """حذف یک آیتم از سبد خرید کاربر."""
    if not require_login(user_id):
        return Response.login_required()
    models.remove_from_cart(user_id, cart_item_id)
    return Response.redirect("/cart")


def handle_checkout(params, user_id):
    """پرداخت نهایی — برای هر آیتم سبد، یک رزرو ایجاد می‌کند.

    مراحل:
    1. گرفتن آیتم‌های سبد خرید کاربر.
    2. برای هر آیتم، بررسی در دسترس بودن اقامتگاه و ایجاد رزرو.
    3. در صورت خطا برای یک آیتم، رزرو بقیه انجام می‌شود و خطا به کاربر نشان داده می‌شود.
    4. در صورت موفقیت کامل، سبد خرید پاک می‌شود و به صفحه‌ی موفقیت هدایت می‌شود.
    """
    if not require_login(user_id):
        return Response.login_required()

    items = models.get_cart_items(user_id)
    if not items:
        return Response.redirect("/cart")

    created_reservations = []
    errors = []

    for item in items:
        property_id = item.get("property_id")
        check_in = item.get("check_in_date")
        check_out = item.get("check_out_date")
        guests = item.get("guests") or 1
        title = item.get("title") or f"#{property_id}"

        if not check_in or not check_out:
            errors.append(f"برای «{title}» تاریخ ورود و خروج مشخص نشده است.")
            continue

        reservation_id, err = models.create_reservation(
            user_id, property_id, check_in, check_out, guests
        )
        if err:
            errors.append(f"برای «{title}»: {err}")
        else:
            created_reservations.append(reservation_id)

    # پاک کردن آیتم‌های سبد که رزرو شدند
    if created_reservations:
        models.clear_cart(user_id)

    if errors and not created_reservations:
        # همه‌ی آیتم‌ها خطا داشتند
        return Response.html(400, generate_error_page(
            400, "؛ ".join(errors), user_id
        ))

    # موفقیت (کامل یا جزئی) — نمایش صفحه‌ی موفقیت
    return Response.html(200, generate_checkout_success_page(
        created_reservations, errors, user_id
    ))
