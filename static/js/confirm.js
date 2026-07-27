/* ============================================================
   confirm.js — جایگزین inline onclick="return confirm(...)"
   ============================================================
   این ماژول به‌صورت خودکار همه‌ی عناصری که ویژگی `data-confirm`
   دارند را پیدا کرده و قبل از اجرای اقدام پیش‌فرضشان (کلیک روی
   لینک یا submit فرم)، یک confirm dialog به کاربر نشان می‌دهد.
   اگر کاربر لغو کند، اقدام متوقف می‌شود.

   این ماژول مستقلاً روی DOMContentLoaded خودش را مقداردهی می‌کند.
   برای فعال‌سازی روی یک صفحه، کافی است template آن صفحه این فایل را
   با <script src="/static/js/confirm.js"></script> import کند.

   نحوه استفاده در HTML:
   ------------------------------------------------------------
   <!-- روی لینک (که با href ریدایرکت می‌شود) -->
   <a href="/cart/5/remove" data-confirm="این آیتم از سبد حذف شود؟">حذف</a>

   <!-- روی دکمه‌ی submit داخل فرم -->
   <form action="/property/1/images/3/delete" method="POST">
       <button type="submit" data-confirm="این تصویر حذف شود؟">حذف</button>
   </form>
   ------------------------------------------------------------
   نکته: اگر `data-confirm` روی خود <form> باشد، هنگام submit بررسی
   می‌شود. اگر روی دکمه‌ی submit یا لینک باشد، هنگام کلیک بررسی
   می‌شود. هر دو حالت پشتیبانی می‌شود.
   ============================================================ */

(function () {
    "use strict";

    function init(root) {
        root = root || document;

        // ۱. لینک‌ها و دکمه‌هایی که data-confirm دارند → روی click
        var triggers = root.querySelectorAll("a[data-confirm], button[type='submit'][data-confirm], button[data-confirm]:not([type='submit'])");
        triggers.forEach(function (el) {
            if (el.__confirmAttached) return;
            el.__confirmAttached = true;
            el.addEventListener("click", function (e) {
                var msg = el.getAttribute("data-confirm") || "آیا مطمئن هستید؟";
                if (!window.confirm(msg)) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
        });

        // ۲. فرم‌هایی که data-confirm دارند → روی submit
        var forms = root.querySelectorAll("form[data-confirm]");
        forms.forEach(function (form) {
            if (form.__confirmAttached) return;
            form.__confirmAttached = true;
            form.addEventListener("submit", function (e) {
                var msg = form.getAttribute("data-confirm") || "آیا مطمئن هستید؟";
                if (!window.confirm(msg)) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
        });
    }

    // API عمومی
    window.ConfirmDialog = { init: init };

    // مقداردهی خودکار روی DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(document); });
    } else {
        init(document);
    }
})();
