/* ============================================================
   image-upload.js — مدیریت پیش‌نمایش و انتخاب تصاویر (Drop Zone)
   ============================================================
   این ماژول به‌صورت خودکار همه‌ی inputهای دارای کلاس
   `image-input` را پیدا کرده و:
   ۱. پیش‌نمایش تصاویر انتخاب‌شده را قبل از آپلود نشان می‌دهد.
   ۲. محدودیت تعداد تصاویر (data-max) را اعمال می‌کند.
   ۳. دکمه‌ی حذف برای هر پیش‌نمایش نشان می‌دهد.
   ۴. ترتیب اولین تصویر را به‌عنوان «شاخص» مشخص می‌کند.
   ۵. از Drag & Drop پشتیبانی می‌کند.
   ۶. شمارنده‌ی تعداد تصاویر انتخاب‌شده را به‌روز می‌کند.

   این ماژول خودش را در `window.JabamanModules` ثبت می‌کند تا
   `main.js` آن را init کند.

   نکته: این اسکریپت فقط پیش‌نمایش است؛ فایل‌های واقعی توسط FormData
   هنگام submit فرم ارسال می‌شوند. به‌جای حذف از input.files (که
   در مرورگرها read-only است)، از یک لیست جداگانه‌ی File استفاده
   می‌کنیم و هنگام submit آن‌ها را به input.files برمی‌گردانیم.
   ============================================================ */
(function () {
    "use strict";

    var MAX_IMAGES = 3;  // پیش‌فرض؛ با data-max روی input قابل تغییر است
    var FA_DIGITS = ['۰','۱','۲','۳','۴','۵','۶','۷','۸','۹'];

    function toFa(n) {
        return String(n).split('').map(function (d) {
            return FA_DIGITS[+d] || d;
        }).join('');
    }

    function init() {
        var inputs = document.querySelectorAll("input.image-input[type='file']");
        for (var i = 0; i < inputs.length; i++) {
            setupInput(inputs[i]);
        }
    }

    function setupInput(input) {
        var max = parseInt(input.getAttribute("data-max"), 10);
        if (isNaN(max) || max <= 0) max = MAX_IMAGES;
        var previewContainerId = input.getAttribute("data-preview-target");
        var previewContainer = previewContainerId
            ? document.getElementById(previewContainerId)
            : findNextPreviewContainer(input);

        // پیدا کردن dropzone (والد input که کلاس image-dropzone دارد)
        var dropzone = input.closest(".image-dropzone");

        // ذخیره‌ی فایل‌های انتخاب‌شده در یک آرایه (چون input.files read-only است)
        var selectedFiles = [];

        function updateCounter() {
            // به‌روزرسانی شمارنده در label
            var formGroup = input.closest(".form-group");
            if (!formGroup) return;
            var counter = formGroup.querySelector(".image-counter-badge");
            if (counter) {
                counter.textContent = toFa(selectedFiles.length) + " از " + toFa(max);
            }
        }

        function addFiles(fileList) {
            for (var i = 0; i < fileList.length; i++) {
                if (selectedFiles.length >= max) {
                    alert("حداکثر " + toFa(max) + " تصویر می‌توانید آپلود کنید.");
                    break;
                }
                var f = fileList[i];
                // اعتبارسنجی نوع
                if (!f.type.startsWith("image/")) {
                    alert("فقط فایل تصویری مجاز است: " + f.name);
                    continue;
                }
                // اعتبارسنجی اندازه (۵MB)
                if (f.size > 5 * 1024 * 1024) {
                    alert("اندازه‌ی فایل بیش از حد بزرگ است (حداکثر ۵MB): " + f.name);
                    continue;
                }
                // جلوگیری از تکرار (بر اساس نام + اندازه)
                var isDuplicate = selectedFiles.some(function (sf) {
                    return sf.name === f.name && sf.size === f.size;
                });
                if (isDuplicate) continue;
                selectedFiles.push(f);
            }
            // پاک‌کردن input (تا کاربر بتواند فایل‌های دیگر هم انتخاب کند)
            input.value = "";
            // به‌روزرسانی پیش‌نمایش
            renderPreviews(previewContainer, selectedFiles, max, input, dropzone);
            updateCounter();
            // به‌روزرسانی وضعیت dropzone
            if (dropzone) {
                if (selectedFiles.length >= max) {
                    dropzone.classList.add("dropzone-full");
                } else {
                    dropzone.classList.remove("dropzone-full");
                }
            }
        }

        input.addEventListener("change", function () {
            addFiles(input.files);
        });

        // فعال‌سازی Drop Zone
        if (dropzone) {
            // کلیک روی dropzone → باز کردن file picker
            dropzone.addEventListener("click", function (e) {
                // اگر کلیک روی دکمه‌ی حذف پیش‌نمایش بود، کاری نکن
                if (e.target.closest(".image-preview-remove")) return;
                // فقط اگر روی دکمه‌ی واقعی dropzone یا خود dropzone کلیک شد
                input.click();
            });

            // جلوگیری از رفتار پیش‌فرض dragover (تا drop اتفاق بیفتد)
            dropzone.addEventListener("dragover", function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("dropzone-dragover");
            });
            dropzone.addEventListener("dragenter", function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("dropzone-dragover");
            });
            dropzone.addEventListener("dragleave", function (e) {
                e.preventDefault();
                e.stopPropagation();
                // فقط اگر از dropzone خارج شد (نه از یک فرزند)
                if (e.target === dropzone) {
                    dropzone.classList.remove("dropzone-dragover");
                }
            });
            dropzone.addEventListener("drop", function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove("dropzone-dragover");
                if (e.dataTransfer && e.dataTransfer.files) {
                    addFiles(e.dataTransfer.files);
                }
            });
        }

        // هنگام submit فرم، فایل‌های selectedFiles را به input.files برمی‌گردانیم
        var form = input.closest("form");
        if (form) {
            form.addEventListener("submit", function (e) {
                // اگر auth.js قبلاً preventDefault کرده، ما هم نیازی به کار نداریم
                // اما برای اطمینان، فایل‌ها را در input قرار می‌دهیم با DataTransfer.
                try {
                    var dt = new DataTransfer();
                    for (var i = 0; i < selectedFiles.length; i++) {
                        dt.items.add(selectedFiles[i]);
                    }
                    input.files = dt.files;
                } catch (err) {
                    // مرورگر از DataTransfer پشتیبانی نمی‌کند (قدیمی)
                    console.warn("DataTransfer پشتیبانی نمی‌شود:", err);
                }
            }, true);  // capture phase تا قبل از auth.js اجرا شود
        }

        // مقدار اولیه شمارنده
        updateCounter();
    }

    function findNextPreviewContainer(input) {
        // پیدا کردن div با کلاس image-preview-list نزدیک input
        var parent = input.parentElement;
        while (parent) {
            var found = parent.querySelector(".image-preview-list");
            if (found) return found;
            parent = parent.parentElement;
        }
        return null;
    }

    function renderPreviews(container, files, max, input, dropzone) {
        if (!container) return;
        container.innerHTML = "";

        if (files.length === 0) return;

        for (var i = 0; i < files.length; i++) {
            (function (file, idx) {
                var item = document.createElement("div");
                item.className = "image-preview-item";

                var img = document.createElement("img");
                img.alt = file.name;
                img.loading = "lazy";
                var reader = new FileReader();
                reader.onload = function (e) {
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
                item.appendChild(img);

                if (idx === 0) {
                    var badge = document.createElement("span");
                    badge.className = "image-preview-badge";
                    badge.innerHTML = '<i class="fas fa-star"></i> شاخص';
                    item.appendChild(badge);
                }

                // نمایش نام فایل
                var nameEl = document.createElement("div");
                nameEl.className = "image-preview-name";
                nameEl.textContent = file.name;
                nameEl.title = file.name;
                item.appendChild(nameEl);

                // نمایش حجم فایل
                var sizeEl = document.createElement("div");
                sizeEl.className = "image-preview-size";
                sizeEl.textContent = formatFileSize(file.size);
                item.appendChild(sizeEl);

                var removeBtn = document.createElement("button");
                removeBtn.type = "button";
                removeBtn.className = "image-preview-remove";
                removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                removeBtn.setAttribute("aria-label", "حذف تصویر");
                removeBtn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    files.splice(idx, 1);
                    renderPreviews(container, files, max, input, dropzone);
                    // به‌روزرسانی شمارنده
                    var formGroup = input.closest(".form-group");
                    if (formGroup) {
                        var counter = formGroup.querySelector(".image-counter-badge");
                        if (counter) {
                            counter.textContent = toFa(files.length) + " از " + toFa(max);
                        }
                    }
                    if (dropzone && files.length < max) {
                        dropzone.classList.remove("dropzone-full");
                    }
                });
                item.appendChild(removeBtn);

                container.appendChild(item);
            })(files[i], i);
        }

        // شمارنده پایین
        var counter = document.createElement("div");
        counter.className = "image-preview-counter";
        counter.innerHTML = '<i class="fas fa-check-circle"></i> ' +
            toFa(files.length) + " از " + toFa(max) + " تصویر انتخاب شد";
        container.appendChild(counter);
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }

    function init(root) {
        root = root || document;
        var inputs = root.querySelectorAll("input.image-input[type='file']");
        for (var i = 0; i < inputs.length; i++) {
            // جلوگیری از attach چندباره
            if (inputs[i].__imageUploadAttached) continue;
            inputs[i].__imageUploadAttached = true;
            setupInput(inputs[i]);
        }
    }

    // ثبت در module registry (main.js اجرای init را برعهده دارد)
    window.JabamanModules = window.JabamanModules || [];
    window.JabamanModules.push({ name: "ImageUpload", init: init });

    // API عمومی
    window.ImageUpload = { init: init };
})();
