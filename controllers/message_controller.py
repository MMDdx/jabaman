# controllers/message_controller.py
"""کنترلر پیام — تماس با ما (POST).

مسیرهای تحت پوشش:
- POST /contact                            → ثبت پیام تماس با ما

نکته: نمایش جزئیات پیام در page_controller.py و حذف پیام در admin_controller.py.
"""
import models
from views import generate_error_page

from ._shared import Response, EMAIL_REGEX


def handle_contact(params, wants_json=False):
    """پردازش فرم تماس با ما.

    فیلدهای مورد انتظار:
    - fullname (الزامی)
    - email (اختیاری، در صورت وارد شدن باید معتبر باشد)
    - phone (اختیاری)
    - topic (اختیاری)
    - message_text (الزامی)
    """
    fullname = params.get('fullname', [''])[0].strip()
    email = params.get('email', [''])[0].strip()
    phone = params.get('phone', [''])[0].strip()
    topic = params.get('topic', [''])[0].strip()
    message_text = params.get('message_text', [''])[0].strip()

    if not fullname or not message_text:
        msg = "نام و متن پیام الزامی است."
        if wants_json:
            return Response.json(400, {"success": False, "error": msg})
        return Response.html(400, msg + " <a href='/contact'>بازگشت</a>")
    if email and not EMAIL_REGEX.match(email):
        msg = "ایمیل نامعتبر است."
        if wants_json:
            return Response.json(400, {"success": False, "error": msg})
        return Response.html(400, msg + " <a href='/contact'>بازگشت</a>")

    try:
        models.create_message(fullname, email, phone, topic, message_text)
        if wants_json:
            return Response.json(200, {"success": True, "message": "پیام با موفقیت ثبت شد."})
        return Response.html(200, "پیام با موفقیت ثبت شد. <a href='/'>بازگشت به خانه</a>")
    except Exception as e:
        if wants_json:
            return Response.json(500, {"success": False, "error": str(e)})
        return Response.html(500, generate_error_page(500, str(e)))
