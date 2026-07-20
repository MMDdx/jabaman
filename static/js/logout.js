/* ============================================================
   logout.js — پاک‌کردن کوکی نشست و ریدایرکت به صفحه اصلی
   ============================================================
   این فایل فقط در صفحه‌ی /logout بارگذاری می‌شود.
   کار آن:
     1) پاک‌کردن کوکی session_id در سمت کلاینت (اضافه بر Set-Cookie سرور)
     2) ریدایرکت کاربر به صفحه اصلی (/) پس از یک مکث کوتاه
   ============================================================ */

(function () {
    "use strict";

    /** پاک‌کردن کوکی با تنظیم max-age=0 */
    function clearSessionCookie() {
        document.cookie = "session_id=; path=/; max-age=0; SameSite=Lax";
        // پاک‌کردن دامنه‌ی والد هم (در صورت نیاز)
        document.cookie = "session_id=; path=/; domain=" + window.location.hostname + "; max-age=0";
    }

    /** ریدایرکت به صفحه اصلی پس از یک مکث کوتاه */
    function redirectToHome() {
        // مکث ۸۰۰ms تا spinner دیده شود و سپس ریدایرکت
        setTimeout(function () {
            window.location.href = "/";
        }, 800);
    }

    // اجرای مراحل پس از لود شدن DOM
    function init() {
        clearSessionCookie();
        redirectToHome();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();