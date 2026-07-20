/* ============================================================
   main.js — اسکریپت عمومی سایت جابامن
   ============================================================
   این فایل در همه‌ی صفحات بارگذاری می‌شود و شامل:
     1) مدیریت خطای بارگذاری تصاویر (به‌جای onerror در HTML)
     2) هایلایت لینک فعال در نوار ناوبری
     3) بستن منوی موبایل با کلیک خارج از منو (در صورت وجود)
   ============================================================ */

(function () {
    "use strict";

    /* ---------- ۱) مدیریت خطای بارگذاری تصاویر ----------
       هر تگ <img> که کلاس logo-img یا کلاس fallback-hide داشته باشد،
       در صورت شکست بارگذاری مخفی می‌شود.
       این کار به‌جای استفاده از onerror="this.style.display='none'" در HTML است.
    */
    function setupImageFallback() {
        var imgs = document.querySelectorAll("img.logo-img, img.fallback-hide");
        imgs.forEach(function (img) {
            img.addEventListener("error", function () {
                img.style.display = "none";
            });
        });
    }

    /* ---------- ۲) هایلایت لینک فعال در ناوبری ----------
       لینکی که href آن با مسیر فعلی همخوانی داشته باشد،
       کلاس active می‌گیرد.
    */
    function highlightActiveNav() {
        var currentPath = window.location.pathname;
        var navLinks = document.querySelectorAll(".main-nav a, .footer-col a");
        navLinks.forEach(function (link) {
            var href = link.getAttribute("href");
            if (!href || href === "#") return;
            // حذف اسلッシュ انتهایی برای مقایسه
            var normalizedHref = href.replace(/\/$/, "");
            var normalizedPath = currentPath.replace(/\/$/, "");
            if (normalizedHref === normalizedPath) {
                link.classList.add("active");
            }
        });
    }

    /* ---------- ۳) فعال‌سازی tooltip ساده برای عناصر با data-tooltip ----------
       (در صورت استفاده در آینده)
    */
    function setupTooltips() {
        var tooltipEls = document.querySelectorAll("[data-tooltip]");
        tooltipEls.forEach(function (el) {
            el.addEventListener("mouseenter", function () {
                var text = el.getAttribute("data-tooltip");
                if (!text) return;
                var tip = document.createElement("div");
                tip.className = "simple-tooltip";
                tip.textContent = text;
                document.body.appendChild(tip);
                var rect = el.getBoundingClientRect();
                tip.style.position = "absolute";
                tip.style.top = (rect.top + window.scrollY - 32) + "px";
                tip.style.left = (rect.left + window.scrollX + rect.width / 2) + "px";
                tip.style.transform = "translateX(-50%)";
                el._tooltip = tip;
            });
            el.addEventListener("mouseleave", function () {
                if (el._tooltip) {
                    el._tooltip.remove();
                    el._tooltip = null;
                }
            });
        });
    }

    /* ---------- اجرای همه‌ی تنظیمات ---------- */
    function init() {
        setupImageFallback();
        highlightActiveNav();
        setupTooltips();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    // API عمومی (در صورت نیاز به استفاده دستی)
    window.JabamanMain = {
        setupImageFallback: setupImageFallback,
        highlightActiveNav: highlightActiveNav
    };
})();