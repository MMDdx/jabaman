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