/* ============================================================
   main.js — Bootstrap مرکزی پروژه‌ی جابامن
   ============================================================
   این فایل در همه‌ی صفحات بارگذاری می‌شود و نقش «dispatch» دارد.

   ----- معماری Module Registry -----
   هر فایل JS (مثل auth.js, image-upload.js, property_gallery.js, ...)
   خودش را در `window.JabamanModules` ثبت می‌کند:

       window.JabamanModules.push({
           name: "ModuleName",
           init: function (root) { ... }
       });

   main.js پس از لود شدن DOM، همه‌ی ماژول‌های ثبت‌شده را به‌ترتیب init
   می‌کند. هر ماژول با querySelector تشخیص می‌دهد که آیا المان مورد
   نیازش روی این صفحه هست یا نه. اگر نبود، یک noop است.

   ----- مزایا -----
   ۱. هر صفحه فقط `<script src="/static/js/main.js">` را شامل می‌شود
      (به‌علاوه‌ی فایل‌های feature-specific که لازم دارند).
   ۲. اضافه‌کردن feature جدید = ساخت فایل JS + import در template +
      ثبت در registry. نیازی به ویرایش main.js نیست.
   ۳. re-init پس از AJAX: می‌توان `window.JabamanInit()` را صدا زد
      تا ماژول‌ها روی DOM جدید هم اجرا شوند.
   ============================================================ */

(function () {
    "use strict";

    // ----- ماژول‌های داخلی main.js -----
    // این‌ها کارهای سراسری هستند که همیشه لازم‌اند و در همین فایل تعریف می‌شوند.

    /**
     * مدیریت خطای بارگذاری تصاویر.
     * هر <img> با کلاس logo-img یا fallback-hide در صورت شکست بارگذاری مخفی می‌شود.
     * جایگزین onerror="this.style.display='none'" در HTML.
     */
    function setupImageFallback(root) {
        var imgs = root.querySelectorAll("img.logo-img, img.fallback-hide");
        imgs.forEach(function (img) {
            // جلوگیری از attach چندباره
            if (img.__fallbackAttached) return;
            img.__fallbackAttached = true;
            img.addEventListener("error", function () {
                img.style.display = "none";
            });
        });
    }

    /**
     * هایلایت لینک فعال در نوار ناوبری.
     */
    function highlightActiveNav(root) {
        var currentPath = window.location.pathname;
        var navLinks = root.querySelectorAll(".main-nav a, .footer-col a");
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
     * فعال‌سازی tooltip ساده برای عناصر با data-tooltip.
     */
    function setupTooltips(root) {
        var tooltipEls = root.querySelectorAll("[data-tooltip]");
        tooltipEls.forEach(function (el) {
            if (el.__tooltipAttached) return;
            el.__tooltipAttached = true;
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

    // register internal modules
    window.JabamanModules = window.JabamanModules || [];
    window.JabamanModules.push({ name: "ImageFallback", init: setupImageFallback });
    window.JabamanModules.push({ name: "ActiveNav",     init: highlightActiveNav });
    window.JabamanModules.push({ name: "Tooltips",      init: setupTooltips });

    // ----- bootstrap -----
    /**
     * init همه‌ی ماژول‌های ثبت‌شده در registry.
     * پارامتر `root` به‌صورت پیش‌فرض document است؛ می‌توان برای re-init
     * روی یک زیر-درخت DOM (مثلاً پس از AJAX) آن را به یک element داد.
     */
    function initAll(root) {
        root = root || document;
        var modules = window.JabamanModules || [];
        for (var i = 0; i < modules.length; i++) {
            try {
                if (typeof modules[i].init === "function") {
                    modules[i].init(root);
                }
            } catch (err) {
                console.error("[Jabaman] module init failed:", modules[i].name, err);
            }
        }
    }

    // اجرای initAll پس از آماده‌شدن DOM
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { initAll(document); });
    } else {
        initAll(document);
    }

    // API عمومی برای re-init دستی (مثلاً بعد از AJAX)
    window.JabamanInit = initAll;
})();
