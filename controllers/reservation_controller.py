# controllers/reservation_controller.py
"""کنترلر رزرو — لغو رزرو توسط کاربر.

مسیرهای تحت پوشش:
- GET /reservation/<int:id>/cancel         → لغو رزرو توسط مالک رزرو

نکته: لغو رزرو توسط ادمین در admin_controller.py است.
"""
import models
from views import generate_error_page

from ._shared import Response, require_login


def cancel_reservation(reservation_id, user_id):
    """لغو رزرو توسط کاربر — فقط مالک رزرو می‌تواند لغو کند."""
    if not require_login(user_id):
        return Response.login_required()

    ok, err = models.cancel_reservation(reservation_id, user_id=user_id)
    if not ok:
        return Response.html(400, generate_error_page(400, err, user_id))
    return Response.redirect("/reservations")
