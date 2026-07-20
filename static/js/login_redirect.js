/* ============================================================
   login_redirect.js — ریدایرکت به صفحه ورود پس از مکث کوتاه
   ============================================================
   این فایل در صفحه‌ی «نیاز به ورود» بارگذاری می‌شود.
   کار آن: ریدایرکت کاربر را به /login پس از ۲ ثانیه انجام می‌دهد.
   ============================================================ */

(function () {
    "use strict";

    function redirectToLogin() {
        setTimeout(function () {
            window.location.href = "/login";
        }, 2000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", redirectToLogin);
    } else {
        redirectToLogin();
    }
})();