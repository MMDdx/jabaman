# views.py
# تولید HTML برای جداول مدیریتی

def generate_table_html(title, columns, rows):
    """یک صفحه HTML کامل با جدول داده‌ها می‌سازد."""
    col_headers = "".join(f"<th>{col}</th>" for col in columns)

    row_cells = ""
    for row in rows:
        cells = "".join(f"<td>{val if val is not None else ''}</td>" for val in row)
        row_cells += f"<tr>{cells}</tr>"

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="table-container">
    <h1 class="page-header">{title}</h1>
    <table class="data-table">
        <thead><tr>{col_headers}</tr></thead>
        <tbody>{row_cells}</tbody>
    </table>
    <p style="text-align:center;margin-top:2rem;"><a href="/">بازگشت</a></p>
</div>
</body>
</html>"""
    return html

def generate_catalog_html(title, properties):
    """صفحه کاتالوگ محصولات با نمایش کارتی"""
    cards = ""
    for prop in properties:
        # prop یک شی Row است؛ می‌توان با نام ستون به آن دسترسی داشت
        prop_id = prop["id"]
        prop_title = prop["title"]
        prop_type = prop["property_type"]
        location = prop["location"]
        price = prop["price_per_night"]
        max_guests = prop["max_guests"]
        bedrooms = prop.get("bedrooms", 0)
        bathrooms = prop.get("bathrooms", 0)
        description = prop.get("description", "") or ""

        # انتخاب آیکون بر اساس نوع اقامتگاه
        type_icons = {
            "villa": "🏡",
            "apartment": "🏢",
            "cottage": "🛖",
            "villa-garden": "🌳",
            "penthouse": "🏙️",
            "other": "🏠"
        }
        icon = type_icons.get(prop_type, "🏠")

        # برش توضیحات
        short_desc = description[:100] + "..." if len(description) > 100 else description

        cards += f"""
        <div class="property-card">
            <div class="card-image">
                <span class="card-type-icon">{icon}</span>
            </div>
            <div class="card-body">
                <h3>{prop_title}</h3>
                <p class="card-location"><i class="fas fa-map-marker-alt"></i> {location}</p>
                <p class="card-details">
                    <span><i class="fas fa-bed"></i> {bedrooms} خواب</span>
                    <span><i class="fas fa-bath"></i> {bathrooms} سرویس</span>
                    <span><i class="fas fa-user"></i> {max_guests} مهمان</span>
                </p>
                <p class="card-description">{short_desc}</p>
                <div class="card-footer">
                    <span class="card-price">{price:,.0f} تومان / شب</span>
                    <a href="/property/{prop_id}" class="card-btn">مشاهده</a>
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="catalog-container">
    <div class="page-header">
        <h1>{title}</h1>
        <p>اقامتگاه‌های موجود برای رزرو</p>
    </div>
    <div class="property-grid">
        {cards}
    </div>
    <p style="text-align:center;margin-top:2rem;">
        <a href="/">بازگشت به خانه</a>
    </p>
</div>
</body>
</html>"""
    return html

# views.py (توابع نمایش فرم ویرایش)
def generate_edit_user_form(user):
    first_name = user["first_name"] if user else ""
    last_name = user["last_name"] if user else ""
    phone = user["phone"] if user else ""
    account_type = user["account_type"] if user else ""

    selected_guest = 'selected' if account_type == 'guest' else ''
    selected_host = 'selected' if account_type == 'host' else ''

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>ویرایش کاربر</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="register-container">
    <div class="page-header">
        <h1>ویرایش کاربر (شناسه ۱)</h1>
    </div>
    <div class="register-card">
        <div class="register-header">
            <i class="fas fa-user-edit"></i>
            <h2>فرم ویرایش</h2>
        </div>
        <form method="POST" action="/admin/users/1/edit" class="register-form">
            <div class="form-row">
                <div class="form-group">
                    <label>نام <span class="required-star">*</span></label>
                    <input type="text" name="first_name" class="form-control" value="{first_name}" required>
                </div>
                <div class="form-group">
                    <label>نام خانوادگی <span class="required-star">*</span></label>
                    <input type="text" name="last_name" class="form-control" value="{last_name}" required>
                </div>
            </div>
            <div class="form-group">
                <label>شماره موبایل <span class="required-star">*</span></label>
                <input type="tel" name="phone" class="form-control" value="{phone}" required pattern="[0-9]{{10,11}}">
            </div>
            <div class="form-group">
                <label>نوع حساب <span class="required-star">*</span></label>
                <select name="account_type" class="form-control" required>
                    <option value="guest" {selected_guest}>مهمان</option>
                    <option value="host" {selected_host}>میزبان</option>
                </select>
            </div>
            <button type="submit" class="submit-btn">ذخیره تغییرات</button>
        </form>
    </div>
    <p style="text-align:center;margin-top:1rem;"><a href="/admin/users">بازگشت به لیست</a></p>
</div>
</body>
</html>"""
    return html


def generate_edit_property_form(property_data):
    title = property_data["title"] if property_data else ""
    description = property_data.get("description", "") or ""
    property_type = property_data["property_type"] if property_data else ""
    location = property_data["location"] if property_data else ""
    price = property_data["price_per_night"] if property_data else ""
    max_guests = property_data["max_guests"] if property_data else ""
    bedrooms = property_data.get("bedrooms", 0) if property_data else 0
    bathrooms = property_data.get("bathrooms", 0) if property_data else 0

    type_options = {
        "villa": "ویلا",
        "apartment": "آپارتمان",
        "cottage": "کلبه",
        "villa-garden": "باغ ویلا",
        "penthouse": "پنت‌هاوس",
        "other": "سایر"
    }
    options_html = ""
    for val, label in type_options.items():
        sel = 'selected' if val == property_type else ''
        options_html += f'<option value="{val}" {sel}>{label}</option>\n'

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>ویرایش اقامتگاه</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="add-listing-container">
    <div class="page-header">
        <h1>ویرایش اقامتگاه (شناسه ۱)</h1>
    </div>
    <div class="form-card">
        <div class="form-header">
            <i class="fas fa-edit"></i>
            <h2>فرم ویرایش</h2>
        </div>
        <form method="POST" action="/admin/properties/1/edit" class="listing-form">
            <div class="form-group">
                <label>عنوان <span class="required-star">*</span></label>
                <input type="text" name="title" class="form-control" value="{title}" required>
            </div>
            <div class="form-group">
                <label>توضیحات</label>
                <textarea name="description" class="form-control" rows="5">{description}</textarea>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>نوع اقامتگاه <span class="required-star">*</span></label>
                    <select name="property_type" class="form-control" required>
                        {options_html}
                    </select>
                </div>
                <div class="form-group">
                    <label>موقعیت <span class="required-star">*</span></label>
                    <input type="text" name="location" class="form-control" value="{location}" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>قیمت هر شب (تومان) <span class="required-star">*</span></label>
                    <input type="number" name="price_per_night" class="form-control" value="{price}" required min="0" step="1000">
                </div>
                <div class="form-group">
                    <label>حداکثر مهمان <span class="required-star">*</span></label>
                    <input type="number" name="max_guests" class="form-control" value="{max_guests}" required min="1">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>اتاق خواب</label>
                    <input type="number" name="bedrooms" class="form-control" value="{bedrooms}" min="0">
                </div>
                <div class="form-group">
                    <label>سرویس بهداشتی</label>
                    <input type="number" name="bathrooms" class="form-control" value="{bathrooms}" min="0">
                </div>
            </div>
            <button type="submit" class="submit-btn">ذخیره تغییرات</button>
        </form>
    </div>
    <p style="text-align:center;margin-top:1rem;"><a href="/admin/properties">بازگشت به لیست</a></p>
</div>
</body>
</html>"""
    return html


def generate_home_html(featured_properties):
    # ساخت کارت‌های اقامتگاه‌های محبوب
    cards_html = ""
    if featured_properties:
        for prop in featured_properties:
            icon_map = {
                "villa": "🏡", "apartment": "🏢", "cottage": "🛖",
                "villa-garden": "🌳", "penthouse": "🏙️", "other": "🏠"
            }
            icon = icon_map.get(prop["property_type"], "🏠")
            location = prop["location"] or "مکان نامشخص"
            price = prop["price_per_night"] or 0
            cards_html += f"""
            <div class="property-card">
                <div class="card-image"><span class="card-type-icon">{icon}</span></div>
                <div class="card-body">
                    <h3>{prop['title']}</h3>
                    <p class="card-location"><i class="fas fa-map-marker-alt"></i> {location}</p>
                    <div class="card-footer">
                        <span class="card-price">{price:,.0f} تومان / شب</span>
                        <a href="/catalog" class="card-btn">مشاهده</a>
                    </div>
                </div>
            </div>
            """
    else:
        cards_html = '<p style="text-align:center;grid-column:1/-1;">هنوز اقامتگاهی ثبت نشده است.</p>'

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>پلتفرم اجاره اقامتگاه - صفحه اصلی</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <!-- هدر / ناوبری -->
    <header class="main-header">
        <div class="header-container">
            <a href="/" class="logo">🏡 اقامتگاه‌یاب</a>
            <nav class="main-nav">
                <a href="/">خانه</a>
                <a href="/catalog">اقامتگاه‌ها</a>
                <a href="/contact">تماس با ما</a>
                <a href="/register" class="btn-outline">ثبت‌نام</a>
                <a href="/login" class="btn-primary">ورود</a>
            </nav>
        </div>
    </header>

    <!-- بخش Hero -->
    <section class="hero">
        <div class="hero-content">
            <h1>اقامتگاه رویایی‌ات را پیدا کن</h1>
            <p>از ویلاهای ساحلی تا کلبه‌های جنگلی، بهترین اقامتگاه‌ها برای سفری خاطره‌انگیز</p>
            <div class="hero-buttons">
                <a href="/catalog" class="btn-primary btn-lg">مشاهده اقامتگاه‌ها</a>
                <a href="/register" class="btn-outline btn-lg">میزبان شوید</a>
            </div>
        </div>
    </section>

    <!-- بخش ویژگی‌ها -->
    <section class="features">
        <div class="container">
            <h2>چرا اقامتگاه‌یاب؟</h2>
            <div class="features-grid">
                <div class="feature-item">
                    <i class="fas fa-shield-alt"></i>
                    <h3>امن و قابل اعتماد</h3>
                    <p>تأیید هویت میزبانان و مهمانان برای اطمینان خاطر شما</p>
                </div>
                <div class="feature-item">
                    <i class="fas fa-wallet"></i>
                    <h3>پرداخت آسان</h3>
                    <p>پرداخت امن آنلاین و پشتیبانی ۲۴ ساعته</p>
                </div>
                <div class="feature-item">
                    <i class="fas fa-star"></i>
                    <h3>بهترین انتخاب‌ها</h3>
                    <p>اقامتگاه‌های متنوع با بهترین قیمت و امتیاز کاربران</p>
                </div>
                <div class="feature-item">
                    <i class="fas fa-headset"></i>
                    <h3>پشتیبانی همیشگی</h3>
                    <p>تیم پشتیبانی آماده پاسخگویی در تمام روزهای هفته</p>
                </div>
            </div>
        </div>
    </section>

    <!-- اقامتگاه‌های محبوب -->
    <section class="featured-properties">
        <div class="container">
            <h2>اقامتگاه‌های محبوب</h2>
            <div class="property-grid">
                {cards_html}
            </div>
            <div class="text-center" style="margin-top:2rem;">
                <a href="/catalog" class="btn-primary">مشاهده همه اقامتگاه‌ها</a>
            </div>
        </div>
    </section>

    <!-- فوتر -->
    <footer class="main-footer">
        <div class="container footer-content">
            <div class="footer-col">
                <h3>اقامتگاه‌یاب</h3>
                <p>بزرگترین پلتفرم اجاره اقامتگاه در ایران</p>
            </div>
            <div class="footer-col">
                <h4>لینک‌های مفید</h4>
                <a href="/catalog">اقامتگاه‌ها</a>
                <a href="/contact">تماس با ما</a>
                <a href="#">قوانین و مقررات</a>
            </div>
            <div class="footer-col">
                <h4>شبکه‌های اجتماعی</h4>
                <div class="social-links">
                    <a href="#"><i class="fab fa-instagram"></i></a>
                    <a href="#"><i class="fab fa-telegram"></i></a>
                    <a href="#"><i class="fab fa-twitter"></i></a>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© ۲۰۲۵ تمام حقوق محفوظ است.</p>
        </div>
    </footer>
</body>
</html>"""
    return html


# views.py (توابع جدید)

def generate_property_detail(property_data):
    """صفحه نمایش جزئیات یک اقامتگاه"""
    if not property_data:
        return generate_error_page(404, "اقامتگاه مورد نظر یافت نشد.")

    icon_map = {
        "villa": "🏡", "apartment": "🏢", "cottage": "🛖",
        "villa-garden": "🌳", "penthouse": "🏙️", "other": "🏠"
    }
    icon = icon_map.get(property_data["property_type"], "🏠")

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{property_data['title']} | اقامتگاه‌یاب</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="detail-container">
    <div class="detail-header">
        <span class="detail-icon">{icon}</span>
        <div>
            <h1>{property_data['title']}</h1>
            <p class="detail-location"><i class="fas fa-map-marker-alt"></i> {property_data['location']}</p>
        </div>
    </div>
    <div class="detail-info">
        <div class="info-box"><i class="fas fa-bed"></i> {property_data.get('bedrooms', 0)} خواب</div>
        <div class="info-box"><i class="fas fa-bath"></i> {property_data.get('bathrooms', 0)} سرویس</div>
        <div class="info-box"><i class="fas fa-user"></i> {property_data['max_guests']} مهمان</div>
    </div>
    <div class="detail-price">{property_data['price_per_night']:,.0f} تومان / شب</div>
    <div class="detail-description">{property_data.get('description', '') or 'توضیحاتی ثبت نشده است.'}</div>
    <p style="text-align:center;margin-top:2rem;">
        <a href="/catalog" class="btn-primary">بازگشت به کاتالوگ</a>
    </p>
</div>
</body>
</html>"""
    return html


def generate_message_detail(message_data):
    """صفحه نمایش جزئیات یک پیام"""
    if not message_data:
        return generate_error_page(404, "پیام مورد نظر یافت نشد.")

    read_status = "خوانده شده" if message_data['is_read'] else "خوانده نشده"
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>پیام از {message_data['fullname']}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="message-detail-container">
    <h1>پیام از {message_data['fullname']}</h1>
    <div class="message-meta">
        <span><strong>ایمیل:</strong> {message_data.get('email', '—')}</span>
        <span><strong>تلفن:</strong> {message_data.get('phone', '—')}</span>
        <span><strong>موضوع:</strong> {message_data.get('topic', '—')}</span>
        <span><strong>وضعیت:</strong> {read_status}</span>
        <span><strong>تاریخ:</strong> {message_data['created_at']}</span>
    </div>
    <div class="message-body">{message_data['message_text']}</div>
    <p><a href="/admin/messages">بازگشت به لیست پیام‌ها</a></p>
</div>
</body>
</html>"""
    return html


def generate_error_page(status_code, message=""):
    """صفحه خطای سفارشی"""
    if status_code == 404:
        title = "صفحه پیدا نشد"
        description = "متأسفانه صفحه‌ای که به دنبال آن هستید وجود ندارد یا حذف شده است."
    elif status_code == 403:
        title = "دسترسی غیرمجاز"
        description = "شما مجوز مشاهده این صفحه را ندارید."
    elif status_code == 500:
        title = "خطای سرور"
        description = "مشکلی در سرور رخ داده است. لطفاً بعداً تلاش کنید."
    else:
        title = "خطا"
        description = message or "خطایی رخ داده است."

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{title} | اقامتگاه‌یاب</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="error-container">
    <div class="error-code">{status_code}</div>
    <h1>{title}</h1>
    <p>{description}</p>
    <a href="/" class="btn-primary">بازگشت به خانه</a>
</div>
</body>
</html>"""
    return html