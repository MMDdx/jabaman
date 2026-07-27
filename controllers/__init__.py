# controllers/__init__.py
"""پکیج کنترلرها — لایه‌ی Controller در معماری MVC.

تقسیم‌بندی کنترلرها بر اساس دامنه‌ی کاربرد (domain-driven):

- _shared:        utilityهای مشترک (Response, match_route, parse form/multipart,
                  require_login/admin, image helpers, EMAIL_REGEX)
- page:           صفحات عمومی GET (home, catalog, contact, login, register, ...)
- auth:           ورود/ثبت‌نام/خروج
- admin:          پنل ادمین (داشبورد، لیست‌ها، edit/delete)
- property:       افزودن/ویرایش/حذف اقامتگاه و تصاویر
- cart:           سبد خرید و checkout
- wishlist:       لیست علاقه‌مندی‌ها
- comment:        ثبت/حذف نظر
- reservation:    لغو رزرو (کاربر و ادمین)
- message:        تماس با ما + جزئیات پیام + حذف پیام

نکته: router.py هنوز نقش entry-point را برای server.py ایفا می‌کند و فقط
کنترلرهای این پکیج را dispatch می‌کند.
"""

# re-export نمادهای پراستفاده برای راحتی import در router.py
from ._shared import (
    Response,
    match_route,
    parse_form_body,
    wants_json,
    require_login,
    require_admin,
    EMAIL_REGEX,
    allowed_image_filename,
    save_uploaded_image,
    delete_image_file,
    MAX_IMAGE_SIZE,
)
