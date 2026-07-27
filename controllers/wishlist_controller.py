# controllers/wishlist_controller.py
"""کنترلر لیست علاقه‌مندی‌ها — افزودن و حذف.

مسیرهای تحت پوشش:
- POST /wishlist/add                       → افزودن اقامتگاه به لیست
- GET  /wishlist/<int:id>/remove           → حذف از لیست
"""
import models
from views import generate_error_page

from ._shared import Response, require_login


def handle_add_to_wishlist(params, user_id):
    """افزودن یک اقامتگاه به لیست علاقه‌مندی‌های کاربر."""
    if not require_login(user_id):
        return Response.login_required()

    property_id = params.get('property_id', [None])[0]
    if not property_id:
        return Response.html(400, "شناسه اقامتگاه الزامی است")
    try:
        models.add_to_wishlist(user_id, property_id)
        return Response.redirect("/wishlist")
    except Exception as e:
        return Response.html(500, generate_error_page(500, str(e)))


def remove_from_wishlist(wishlist_item_id, user_id):
    """حذف یک اقامتگاه از لیست علاقه‌مندی‌ها."""
    if not require_login(user_id):
        return Response.login_required()
    models.remove_from_wishlist(user_id, wishlist_item_id)
    return Response.redirect("/wishlist")
