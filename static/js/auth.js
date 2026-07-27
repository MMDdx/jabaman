/* ============================================================
   auth.js — اسکریپت مشترک برای فرم‌های AJAX (ورود، ثبت‌نام، تماس، ...)
   ============================================================
   این ماژول به‌صورت خودکار فرم‌هایی که ویژگی `data-ajax-form` دارند
   را پیدا کرده و ارسال آن‌ها را با fetch مدیریت می‌کند.

   این ماژول مستقلاً روی DOMContentLoaded خودش را مقداردهی می‌کند.
   برای فعال‌سازی روی یک صفحه، کافی است template آن صفحه این فایل را
   با <script src="/static/js/auth.js"></script> import کند. هیچ
   registry مرکزی لازم نیست.

   نحوه استفاده در HTML:
   ------------------------------------------------------------
   <form data-ajax-form
         data-success-redirect="/"
         data-success-message="ورود موفقیت‌آمیز بود."
         data-loading-text="در حال ورود..."
         action="/login"
         method="POST">
       <!-- فیلدها -->
   </form>
   <div id="form-message" class="form-message" role="alert" style="display:none;"></div>
   ------------------------------------------------------------

   ویژگی‌های قابل تنظیم روی <form>:
   - data-ajax-form          : فعال‌سازی هندلر (الزامی)
   - data-success-redirect   : URL ریدایرکت بعد از موفقیت (اختیاری،
                              اگر سرور خودش redirect برگرداند از همان استفاده می‌شود)
   - data-success-message    : پیام موفقیت قبل از ریدایرکت (اختیاری)
   - data-loading-text       : متن دکمه هنگام loading (پیش‌فرض: "...")
   ============================================================ */

(function () {
    "use strict";

    /** پیام خطا/موفقیت را در باکس #form-message نمایش می‌دهد. */
    function showMessage(msgBox, text, type) {
        if (!msgBox) return;
        msgBox.textContent = text;
        msgBox.className = "form-message " + (type || "error");
        msgBox.style.display = "block";
        msgBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    /** باکس پیام را مخفی می‌کند. */
    function hideMessage(msgBox) {
        if (!msgBox) return;
        msgBox.style.display = "none";
        msgBox.textContent = "";
    }

    /** وضعیت loading دکمه submit را تنظیم می‌کند. */
    function setLoading(form, isLoading, loadingText) {
        var btn = form.querySelector("button[type='submit']");
        if (!btn) return;
        // ذخیره متن اصلی دکمه (فقط بار اول)
        if (!btn.dataset.originalText) {
            // متن دکمه ممکن است شامل <span> و <i> باشد؛ span را پیدا می‌کنیم
            var span = btn.querySelector("span");
            btn.dataset.originalText = span ? span.textContent : btn.textContent;
        }
        if (isLoading) {
            btn.disabled = true;
            var span = btn.querySelector("span");
            if (span) span.textContent = loadingText || "...";
        } else {
            btn.disabled = false;
            var span2 = btn.querySelector("span");
            if (span2) span2.textContent = btn.dataset.originalText;
        }
    }

    /** تبدیل FormData به URLSearchParams.
     * نکته مهم: اگر FormData را مستقیم به fetch بدهیم، مرورگر آن را به‌صورت
     * multipart/form-data ارسال می‌کند، اما سرور ساده‌ی Python ما فقط
     * application/x-www-form-urlencoded را با urllib.parse.parse_qs تجزیه می‌کند.
     * پس باید URLSearchParams بسازیم.
     */
    function formDataToURLSearchParams(formData) {
        var params = new URLSearchParams();
        formData.forEach(function (value, key) {
            params.append(key, value);
        });
        return params;
    }

    /** اعتبارسنجی سمت کلاینت قبل از ارسال.
     * فقط فیلدهای required و `minlength` و `type="email"` و `type="password"`
     * و `type="tel"` با `pattern` را بررسی می‌کند.
     * اگر خطا بود، پیام برمی‌گرداند؛ در غیر این صورت null.
     */
    function validateForm(form) {
        var inputs = form.querySelectorAll("input, select, textarea");
        for (var i = 0; i < inputs.length; i++) {
            var input = inputs[i];
            var name = input.name || input.id || "";
            var label = form.querySelector("label[for='" + (input.id || "") + "']");
            var labelText = label ? label.textContent.replace("*", "").trim() : name;

            // required
            if (input.hasAttribute("required") && !input.value.trim()) {
                return labelText + " الزامی است.";
            }
            // minlength (فقط برای input متنی)
            if (input.type !== "checkbox" && input.minLength > 0 &&
                input.value.length < input.minLength) {
                return labelText + " باید حداقل " + input.minLength + " کاراکتر باشد.";
            }
            // type=email
            if (input.type === "email" && input.value) {
                var emailRe = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
                if (!emailRe.test(input.value)) {
                    return "ایمیل نامعتبر است.";
                }
            }
            // pattern (فقط tel)
            if (input.type === "tel" && input.value && input.pattern) {
                var re = new RegExp(input.pattern);
                if (!re.test(input.value)) {
                    return labelText + " نامعتبر است.";
                }
            }
        }
        return null;
    }

    /** هندلر submit برای یک فرم. */
    function attachHandler(form) {
        var msgBox = document.getElementById("form-message");
        var loadingText = form.dataset.loadingText || "در حال ارسال...";
        var successMessage = form.dataset.successMessage;
        var successRedirect = form.dataset.successRedirect;
        var action = form.getAttribute("action") || window.location.pathname;

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            hideMessage(msgBox);

            // ۱) اعتبارسنجی سمت کلاینت
            var validationError = validateForm(form);
            if (validationError) {
                showMessage(msgBox, validationError, "error");
                return;
            }

            // ۲) جمع‌آوری داده‌ها
            var formData = new FormData(form);

            // اگر فرم شامل فایل آپلودی است، FormData را مستقیم (multipart) بفرست
            // تا فایل‌ها هم همراهش ارسال شوند. در غیر این صورت URL-encoded.
            var hasFile = form.querySelector("input[type='file']") !== null;
            var body, contentType;
            if (hasFile) {
                body = formData;
                contentType = undefined; // مرورگر خودش boundary تنظیم می‌کند
            } else {
                body = formDataToURLSearchParams(formData);
                contentType = "application/x-www-form-urlencoded";
            }

            // ۳) ارسال با fetch
            setLoading(form, true, loadingText);

            var fetchOpts = {
                method: "POST",
                body: body,
                headers: {
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin"
            };
            // فقط اگر content-type مشخص بود، ست کن (برای multipart مرورگر خودش می‌سازد)
            if (contentType) {
                fetchOpts.headers["Content-Type"] = contentType;
            }

            fetch(action, fetchOpts)
            .then(function (resp) {
                // اگر پاسخ JSON نبود (مثلاً redirect HTML)، متن معمولی برمی‌گردد
                var ct = resp.headers.get("Content-Type") || "";
                if (ct.indexOf("application/json") === -1) {
                    // پاسخ غیر JSON — احتمالاً یک صفحه HTML (مثل redirect).
                    // در این حالت از successRedirect یا location استفاده می‌کنیم.
                    return resp.text().then(function () {
                        return { status: resp.status, data: { success: resp.ok, redirect: successRedirect } };
                    });
                }
                return resp.json().then(function (data) {
                    return { status: resp.status, data: data };
                });
            })
            .then(function (result) {
                var data = result.data || {};
                if (data.success) {
                    // موفقیت
                    var msg = data.message || successMessage || "با موفقیت انجام شد.";
                    showMessage(msgBox, msg, "success");
                    var target = data.redirect || successRedirect || null;
                    if (target) {
                        setTimeout(function () {
                            window.location.href = target;
                        }, 600);
                    } else {
                        setLoading(form, false, loadingText);
                    }
                } else {
                    // خطای اعتبارسنجی سرور
                    showMessage(msgBox, data.error || "خطای ناشناخته رخ داد.", "error");
                    setLoading(form, false, loadingText);
                }
            })
            .catch(function (err) {
                // خطای شبکه یا JSON نامعتبر
                showMessage(msgBox, "ارتباط با سرور برقرار نشد. دوباره تلاش کنید.", "error");
                setLoading(form, false, loadingText);
            });
        });
    }

    /** وقتی DOM آماده شد، همه فرم‌های `data-ajax-form` را attach کن. */
    function init(root) {
        root = root || document;
        var forms = root.querySelectorAll("form[data-ajax-form]");
        for (var i = 0; i < forms.length; i++) {
            // جلوگیری از attach چندباره
            if (forms[i].__authFormAttached) continue;
            forms[i].__authFormAttached = true;
            attachHandler(forms[i]);
        }
    }

    // API عمومی (در صورت نیاز به استفاده دستی، مثلاً بعد از تزریق DOM جدید)
    window.AuthForm = {
        init: init,
        showMessage: showMessage,
        hideMessage: hideMessage,
        validateForm: validateForm
    };

    // مقداردهی خودکار روی DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(document); });
    } else {
        init(document);
    }
})();