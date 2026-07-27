/* ============================================================
   reservation_form.js — فرم رزرو اقامتگاه
   ============================================================
   کارها:
     ۱. پیش‌نمایش زنده‌ی قیمت (تعداد شب × قیمت پایه + هزینه‌ی مهمان اضافی)
     ۲. تنظیم حداقل تاریخ ورود/خروج به امروز
     ۳. اعتبارسنجی قبل از submit (تاریخ، تعداد مهمان، هم‌پوشانی با رزروها)

   نحوه استفاده در HTML:
   ------------------------------------------------------------
   <form data-reservation-form
         data-price-per-night="850000"
         data-max-guests="4"
         data-extra-guest-charge="100000"
         data-reserved-ranges='[{"start":"2026-08-01","end":"2026-08-05"}]'
         action="/cart/add" method="POST">
       <input type="date" name="check_in_date">
       <input type="date" name="check_out_date">
       <input type="number" name="guests" min="1" max="12">
       ...
   </form>
   <div data-price-preview hidden>
       <span data-preview-nights></span>
       <span data-preview-base></span>
       <span data-preview-extra></span>
       <span data-preview-total></span>
   </div>
   ------------------------------------------------------------

   data attributeها روی <form>:
   - data-reservation-form       : فعال‌سازی هندلر (الزامی)
   - data-price-per-night        : قیمت هر شب به تومان
   - data-max-guests             : ظرفیت استاندارد
   - data-extra-guest-charge     : هزینه‌ی هر مهمان اضافی در هر شب
   - data-reserved-ranges        : JSON آرایه‌ی {start, end} از رزروهای موجود

   عناصر UI اختیاری:
   - [data-price-preview]        : باکس پیش‌نمایش (مخفی تا زمان لود)
   - [data-preview-nights]       : نمایش تعداد شب
   - [data-preview-base]         : نمایش قیمت پایه
   - [data-preview-extra-row]    : ردیف هزینه‌ی مهمان اضافی (مخفی اگر مهمان اضافی نیست)
   - [data-preview-extra]        : نمایش هزینه‌ی مهمان اضافی
   - [data-preview-total]        : نمایش مبلغ کل
   ============================================================ */

(function () {
    "use strict";

    var FA_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];

    function fmt(num) {
        return num.toLocaleString("fa-IR");
    }

    function rangesOverlap(aStart, aEnd, bStart, bEnd) {
        // هم‌پوشانی: A.start < B.end AND B.start < A.end
        return new Date(aStart) < new Date(bEnd) && new Date(bStart) < new Date(aEnd);
    }

    function findOverlap(checkIn, checkOut, reservedRanges) {
        for (var i = 0; i < reservedRanges.length; i++) {
            var r = reservedRanges[i];
            if (rangesOverlap(checkIn, checkOut, r.start, r.end)) {
                return r;
            }
        }
        return null;
    }

    function initForm(form) {
        var pricePerNight = parseFloat(form.dataset.pricePerNight) || 0;
        var maxGuests = parseInt(form.dataset.maxGuests, 10) || 1;
        var extraChargePerGuest = parseFloat(form.dataset.extraGuestCharge) || 100000;

        var reservedRanges = [];
        var rangesAttr = form.dataset.reservedRanges;
        if (rangesAttr) {
            try {
                reservedRanges = JSON.parse(rangesAttr);
            } catch (e) {
                console.error("[ReservationForm] invalid reserved-ranges JSON:", e);
            }
        }

        var checkIn = form.querySelector("[name='check_in_date']");
        var checkOut = form.querySelector("[name='check_out_date']");
        var guests = form.querySelector("[name='guests']");
        var preview = form.querySelector("[data-price-preview]");
        var nightsEl = form.querySelector("[data-preview-nights]");
        var baseEl = form.querySelector("[data-preview-base]");
        var extraRow = form.querySelector("[data-preview-extra-row]");
        var extraEl = form.querySelector("[data-preview-extra]");
        var totalEl = form.querySelector("[data-preview-total]");

        if (!checkIn || !checkOut || !guests) return;

        function updatePreview() {
            if (!preview) return;
            if (!checkIn.value || !checkOut.value) {
                preview.style.display = "none";
                return;
            }
            var d1 = new Date(checkIn.value);
            var d2 = new Date(checkOut.value);
            if (isNaN(d1.getTime()) || isNaN(d2.getTime()) || d2 <= d1) {
                preview.style.display = "none";
                return;
            }
            var nights = Math.round((d2 - d1) / (1000 * 60 * 60 * 24));
            if (nights < 1) nights = 1;
            var g = parseInt(guests.value, 10) || 1;
            var base = pricePerNight * nights;
            var extraGuests = Math.max(0, g - maxGuests);
            var extraCharge = extraGuests * extraChargePerGuest * nights;
            var total = base + extraCharge;

            if (nightsEl) nightsEl.textContent = fmt(nights) + " شب";
            if (baseEl)   baseEl.textContent = fmt(base);
            if (extraRow && extraEl) {
                if (extraGuests > 0) {
                    extraRow.style.display = "flex";
                    extraEl.textContent = fmt(extraCharge) + " (" + fmt(extraGuests) +
                        " نفر اضافی × " + fmt(nights) + " شب)";
                } else {
                    extraRow.style.display = "none";
                }
            }
            if (totalEl) totalEl.textContent = fmt(total);
            preview.style.display = "block";
        }

        // bind change events
        checkIn.addEventListener("change", updatePreview);
        checkOut.addEventListener("change", updatePreview);
        guests.addEventListener("input", updatePreview);

        // حداقل تاریخ ورود/خروج = امروز
        var today = new Date().toISOString().split("T")[0];
        checkIn.setAttribute("min", today);
        checkOut.setAttribute("min", today);

        // اعتبارسنجی قبل از submit
        form.addEventListener("submit", function (e) {
            if (!checkIn.value || !checkOut.value) {
                e.preventDefault();
                alert("لطفاً تاریخ ورود و خروج را انتخاب کنید.");
                return;
            }
            var d1 = new Date(checkIn.value);
            var d2 = new Date(checkOut.value);
            if (d2 <= d1) {
                e.preventDefault();
                alert("تاریخ خروج باید بعد از تاریخ ورود باشد.");
                return;
            }
            var g = parseInt(guests.value, 10) || 0;
            if (g < 1) {
                e.preventDefault();
                alert("تعداد مهمان باید حداقل ۱ باشد.");
                return;
            }
            // بررسی هم‌پوشانی با رزروهای موجود
            var overlap = findOverlap(checkIn.value, checkOut.value, reservedRanges);
            if (overlap) {
                e.preventDefault();
                alert("بازه‌ی انتخابی شما از " + overlap.start + " تا " + overlap.end +
                      " با رزروی موجود هم‌پوشانی دارد.\nلطفاً بازه‌ی دیگری انتخاب کنید.");
                return;
            }
        });

        // محاسبه‌ی اولیه (اگر تاریخ از قبل پر شده بود)
        updatePreview();
    }

    function init(root) {
        var forms = (root || document).querySelectorAll("form[data-reservation-form]");
        for (var i = 0; i < forms.length; i++) {
            initForm(forms[i]);
        }
    }

    // API عمومی
    window.ReservationForm = { init: init };

    // مقداردهی خودکار روی DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(document); });
    } else {
        init(document);
    }
})();
