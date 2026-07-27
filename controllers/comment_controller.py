# controllers/comment_controller.py
"""کنترلر نظرات — ثبت نظر جدید.

مسیرهای تحت پوشش:
- POST /comment/add                        → ثبت نظر برای یک اقامتگاه

نکته: حذف نظر در admin_controller.py است (admin-only).
"""
import models

from ._shared import Response, require_login


def handle_add_comment(params, user_id):
    """ثبت نظر جدید برای یک اقامتگاه.

    فیلدهای مورد انتظار:
    - property_id (الزامی)
    - comment_text (الزامی)
    - rating (1..5، پیش‌فرض 5)
    """
    if not require_login(user_id):
        return Response.login_required()

    property_id = params.get('property_id', [None])[0]
    comment_text = params.get('comment_text', [''])[0].strip()
    rating = params.get('rating', ['5'])[0]

    if not property_id or not comment_text:
        return Response.html(400, "شناسه و متن نظر الزامی است")
    try:
        rating_int = max(1, min(5, int(rating)))
        models.add_comment(user_id, property_id, comment_text, rating_int)
        return Response.redirect(f"/property/{property_id}")
    except ValueError:
        return Response.html(400, "امتیاز نامعتبر است")
