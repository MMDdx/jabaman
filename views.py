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