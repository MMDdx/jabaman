/* ============================================================
   main.js — اسکریپت سراسری برای تمام صفحات جابامن
   ============================================================
   نقش این فایل: فقط انجام دو کار سراسری روی هر صفحه‌ای که
   navbar لوگو دارد:
     ۱. مخفی‌کردن خودکار تصاویری که بارگذاری‌شان شکست خورده
        (جایگزین onerror="this.style.display='none'" در HTML).
     ۲. هایلایت لینک فعال در نوار ناوبری.

   ----- معماری جدید -----
   این فایل دیگر یک «مرکز dispatch» برای ماژول‌های دیگر نیست.
   هر فایل JS اختصاصی (auth.js, image-upload.js, property_gallery.js,
   reservation_form.js, logout.js, login_redirect.js) خودش را روی
   DOMContentLoaded مقداردهی می‌کند و مستقلاً به المان‌های مورد
   نیازش event listener می‌چسباند. برای این کار، فقط کافی است
   template مربوطه آن فایل JS را import کند — نیازی به ثبت در
   هیچ registry یا اجرای initAll مرکزی نیست.
   ============================================================ */

(function () {
    "use strict";

    /**
     * مدیریت خطای بارگذاری تصاویر.
     * هر <img> با کلاس logo-img یا fallback-hide در صورت شکست بارگذاری مخفی می‌شود.
     * جایگزین onerror="this.style.display='none'" در HTML.
     */
    function setupImageFallback() {
        var imgs = document.querySelectorAll("img.logo-img, img.fallback-hide");
        imgs.forEach(function (img) {
            if (img.__fallbackAttached) return;
            img.__fallbackAttached = true;
            img.addEventListener("error", function () {
                img.style.display = "none";
            });
        });
    }

    /**
     * هایلایت لینک فعال در نوار ناوبری.
     * مسیر جاری صفحه را با href هر لینک در navbar/footer مقایسه می‌کند
     * و در صورت تطابق، کلاس active را اضافه می‌کند.
     */
    function highlightActiveNav() {
        var currentPath = window.location.pathname;
        var navLinks = document.querySelectorAll(".main-nav a, .footer-col a");
        navLinks.forEach(function (link) {
            var href = link.getAttribute("href");
            if (!href || href === "#") return;
            var normalizedHref = href.replace(/\/$/, "");
            var normalizedPath = currentPath.replace(/\/$/, "");
            if (normalizedHref === normalizedPath) {
                link.classList.add("active");
            }
        });
    }

    /**
     * اجرای دو کار سراسری پس از آماده‌شدن DOM.
     * در صفحاتی که DOM هنوز در حال parsing است، روی DOMContentLoaded
     * صبر می‌کنیم؛ در غیر این صورت (script آخر body) همین الان اجرا می‌شود.
     */
    function init() {
        setupImageFallback();
        highlightActiveNav();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
