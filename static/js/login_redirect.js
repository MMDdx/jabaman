/* ============================================================
   login_redirect.js — ریدایرکت به صفحه ورود پس از مکث کوتاه
   ============================================================
   این ماژول در صفحه‌ی «نیاز به ورود» فعال می‌شود.
   برای فعال‌سازی، کافیست یک عنصر با attribute `data-login-redirect`
   یا id="login-redirect-page" روی صفحه باشد.

   کار آن: ریدایرکت کاربر را به /login پس از ۲ ثانیه انجام می‌دهد.

   این ماژول مستقلاً روی DOMContentLoaded خودش را مقداردهی می‌کند.
   ============================================================ */

(function () {
    "use strict";

    function init(root) {
        root = root || document;
        var trigger = root.querySelector("[data-login-redirect], #login-redirect-page, .login-redirect-page");
        if (!trigger) return;
        // جلوگیری از اجرای دوباره
        if (window.__loginRedirectDone) return;
        window.__loginRedirectDone = true;

        setTimeout(function () {
            window.location.href = "/login";
        }, 2000);
    }

    // API عمومی
    window.LoginRedirect = { init: init };

    // مقداردهی خودکار روی DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(document); });
    } else {
        init(document);
    }
})();
