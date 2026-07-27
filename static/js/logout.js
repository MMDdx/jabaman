/* ============================================================
   logout.js — پاک‌کردن کوکی نشست و ریدایرکت به صفحه اصلی
   ============================================================
   این ماژول فقط در صفحه‌ی /logout فعال می‌شود (با وجود data-logout-page
   یا خود وجود کوکی session_id تشخیص داده نمی‌شود — فقط یک عنصر با
   attribute `data-logout-trigger` را فعال می‌کند).

   برای backward-compat: اگر صفحه شامل عنصری با id="logout-page" یا
   کلاس "logout-page" باشد، تابع فعال می‌شود.

   کار آن:
     1) پاک‌کردن کوکی session_id در سمت کلاینت (اضافه بر Set-Cookie سرور)
     2) ریدایرکت کاربر به صفحه اصلی (/) پس از یک مکث کوتاه

   نکته: این ماژول خودش را در `window.JabamanModules` ثبت می‌کند.
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

    function init(root) {
        root = root || document;
        // فقط در صفحه‌ی /logout فعال می‌شود
        var trigger = root.querySelector("[data-logout-trigger], #logout-page, .logout-page");
        if (!trigger) return;
        // جلوگیری از اجرای دوباره
        if (window.__logoutDone) return;
        window.__logoutDone = true;
        clearSessionCookie();
        redirectToHome();
    }

    // ثبت در module registry
    window.JabamanModules = window.JabamanModules || [];
    window.JabamanModules.push({ name: "LogoutRedirect", init: init });

    // API عمومی
    window.LogoutRedirect = { init: init };
})();
