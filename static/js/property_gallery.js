/* ============================================================
   property_gallery.js — گالری تصاویر اقامتگاه
   ============================================================
   کارها:
     ۱. نمایش تصویر انتخاب‌شده در main img
     ۲. ناوبری با دکمه‌های قبلی/بعدی
     ۳. ناوبری با کیبورد (Arrow Left/Right با توجه به RTL)
     ۴. کلیک روی thumbnail برای انتخاب مستقیم

   نحوه استفاده در HTML:
   ------------------------------------------------------------
   <div class="property-gallery" data-gallery>
       <div class="gallery-main">
           <img id="gallery-main-img" src="..." class="gallery-main-img">
           <button type="button" class="gallery-nav gallery-nav-prev" data-gallery-prev>...</button>
           <button type="button" class="gallery-nav gallery-nav-next" data-gallery-next>...</button>
           <span class="gallery-counter">
               <span data-gallery-current>۱</span> / ۳
           </span>
       </div>
       <div class="gallery-thumbs">
           <button type="button" class="gallery-thumb" data-gallery-thumb data-index="0">
               <img src="..." alt="...">
           </button>
           ...
       </div>
   </div>
   ------------------------------------------------------------
   نکته: لیست URL تصاویر باید در یک تگ با `data-gallery-images`
   به‌صورت JSON آرایه‌ای از stringها قرار گیرد:
       <div data-gallery-images='["/img1.jpg","/img2.jpg"]' hidden></div>
   ============================================================ */

(function () {
    "use strict";

    var FA_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];

    function toFa(n) {
        return String(n).split('').map(function (d) {
            return FA_DIGITS[+d] || d;
        }).join('');
    }

    function initGallery(root) {
        // خواندن لیست URLها از data attribute
        var imagesSource = root.querySelector("[data-gallery-images]");
        var images = [];
        if (imagesSource) {
            try {
                images = JSON.parse(imagesSource.textContent || "[]");
            } catch (e) {
                console.error("[PropertyGallery] invalid JSON:", e);
                return;
            }
        }
        if (!images.length) return;

        var currentIndex = 0;
        var mainImg = root.querySelector("[data-gallery-main]") ||
                      root.querySelector("#gallery-main-img");
        var currentLabel = root.querySelector("[data-gallery-current]") ||
                           root.querySelector("#gallery-current");
        var thumbs = root.querySelectorAll("[data-gallery-thumb]");
        var prevBtn = root.querySelector("[data-gallery-prev]");
        var nextBtn = root.querySelector("[data-gallery-next]");

        function select(idx) {
            if (idx < 0 || idx >= images.length) return;
            currentIndex = idx;
            if (mainImg) mainImg.src = images[idx];
            if (currentLabel) currentLabel.textContent = toFa(idx + 1);
            thumbs.forEach(function (t, i) {
                if (i === idx) t.classList.add("active");
                else t.classList.remove("active");
            });
        }

        function navigate(delta) {
            var next = currentIndex + delta;
            if (next < 0) next = images.length - 1;
            if (next >= images.length) next = 0;
            select(next);
        }

        // attach event handlers
        if (prevBtn) {
            prevBtn.addEventListener("click", function () { navigate(-1); });
        }
        if (nextBtn) {
            nextBtn.addEventListener("click", function () { navigate(1); });
        }
        thumbs.forEach(function (thumb, idx) {
            thumb.addEventListener("click", function () { select(idx); });
        });

        // keyboard navigation (فقط وقتی focus روی input/textarea نیست)
        document.addEventListener("keydown", function (e) {
            var tag = (e.target.tagName || '').toLowerCase();
            if (tag === "input" || tag === "textarea" || tag === "select") return;
            if (e.key === "ArrowLeft")  navigate(1);    // در RTL: چپ → بعدی
            if (e.key === "ArrowRight") navigate(-1);   // در RTL: راست → قبلی
        });

        // backward-compat: توابع عمومی قبلی که در onclick استفاده می‌شدند
        window.gallerySelect = select;
        window.galleryNavigate = navigate;
    }

    function init(root) {
        var galleries = (root || document).querySelectorAll("[data-gallery]");
        for (var i = 0; i < galleries.length; i++) {
            initGallery(galleries[i]);
        }
    }

    // API عمومی
    window.PropertyGallery = { init: init };

    // مقداردهی خودکار روی DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(document); });
    } else {
        init(document);
    }
})();
