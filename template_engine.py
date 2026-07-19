# template_engine.py
"""موتور قالب اختصاصی سبک Jinja2.

تغییرات نسبت به نسخه‌ی قبل:
- HTML escaping خودکار برای جلوگیری از XSS.
- پشتیبانی از sqlite3.Row (نه فقط dict).
- پشتیبانی از فیلتر length: {{ list|length }}.
- پشتیبانی از شرط‌های مقایسه‌ای: {% if var == 'value' %} و {% if not var %}.
- پشتیبانی از حلقه با اندیس {% for i, item in enumerate(items) %}.
- قابلیت{% elif %} و {% else %} در if.
"""
import re
import html
import os
from collections.abc import Mapping

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _get_value(obj, key):
    """دسترسی امن به مقادیر dict، sqlite3.Row یا شیء با attribute.

    اگر کلید وجود نداشت یا مقدار None بود، رشته‌ی خالی برمی‌گرداند.
    """
    if obj is None:
        return ""
    # اگر dict یا Mapping
    if isinstance(obj, Mapping):
        val = obj.get(key, "")
    # اگر sqlite3.Row یا شیء با keys
    elif hasattr(obj, "keys"):
        try:
            val = obj[key]
        except (KeyError, IndexError):
            val = ""
    # در غیر این صورت، تلاش با getattr
    else:
        val = getattr(obj, key, "")
    return "" if val is None else val


def _resolve_expr(expr, context):
    """حل یک عبارت ساده مانند user.first_name یا items|length.

    پشتیبانی از:
    - متغیر ساده: {{ var }}
    - دسترسی با نقطه: {{ obj.attr }}
    - فیلتر length: {{ list|length }}
    - ایندکس عددی: {{ items.0 }}
    """
    expr = expr.strip()

    # فیلتر length
    if "|" in expr:
        parts = expr.split("|", 1)
        var_expr = parts[0].strip()
        filter_name = parts[1].strip()
        val = _resolve_expr(var_expr, context)
        if filter_name == "length":
            try:
                return str(len(val))
            except TypeError:
                return "0"
        # فیلترهای دیگر در آینده
        return str(val)

    # دسترسی با نقطه
    if "." in expr:
        parts = expr.split(".")
        obj = context.get(parts[0])
        for part in parts[1:]:
            if obj is None:
                return ""
            # ایندکس عددی
            if part.isdigit() and isinstance(obj, (list, tuple)):
                try:
                    obj = obj[int(part)]
                except IndexError:
                    return ""
            else:
                obj = _get_value(obj, part)
        return obj

    # متغیر ساده
    val = context.get(expr, "")
    return val if val is not None else ""


def _escape(value):
    """Escape کردن HTML برای جلوگیری از XSS."""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return html.escape(value, quote=True)


def replace_variables(text, context, autoescape=True):
    """جایگزینی تمام {{ expr }} با مقدار حل‌شده.

    اگر autoescape=True باشد (پیش‌فرض)، خروجی escape می‌شود.
    برای غیرفعال‌کردن: {{ expr|safe }}
    """
    def replacer(match):
        expr = match.group(1).strip()
        # فیلتر safe برای غیرفعال‌کردن escape
        if expr.endswith("|safe"):
            expr = expr[:-5].strip()
            val = _resolve_expr(expr, context)
            return str(val) if val is not None else ""
        val = _resolve_expr(expr, context)
        return _escape(val) if autoescape else str(val)
    return re.sub(r'\{\{(.*?)\}\}', replacer, text, flags=re.DOTALL)


def _eval_condition(cond, context):
    """ارزیابی شرط ساده.

    پشتیبانی از:
    - {% if var %}            → truthy check
    - {% if not var %}        → falsy check
    - {% if var == 'value' %} → مقایسه با رشته
    - {% if var != 'value' %}
    - {% if var == 5 %}       → مقایسه با عدد
    """
    cond = cond.strip()

    # not var
    m = re.match(r'^not\s+(\w+(?:\.\w+)*)$', cond)
    if m:
        val = _resolve_expr(m.group(1), context)
        return not val

    # var == value  یا  var != value
    m = re.match(r'^(\w+(?:\.\w+)*)\s*(==|!=)\s*(.+)$', cond)
    if m:
        left = _resolve_expr(m.group(1), context)
        op = m.group(2)
        right_raw = m.group(3).strip()
        # پارس کردن right (رشته با کوتیشن یا عدد)
        if (right_raw.startswith("'") and right_raw.endswith("'")) or \
           (right_raw.startswith('"') and right_raw.endswith('"')):
            right = right_raw[1:-1]
        elif right_raw.isdigit():
            right = int(right_raw)
        else:
            right = _resolve_expr(right_raw, context)
        if op == "==":
            return str(left) == str(right)
        else:
            return str(left) != str(right)

    # حالت ساده: فقط متغیر (truthy check)
    val = _resolve_expr(cond, context)
    return bool(val)


def render_template(template_name, context=None):
    """رندر یک قالب با context داده‌شده.

    از autoescape به‌صورت پیش‌فرض استفاده می‌شود.
    برای محتوای trusted می‌توان از فیلتر |safe استفاده کرد.
    """
    if context is None:
        context = {}

    filepath = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(filepath):
        return f"Template {template_name} not found."

    with open(filepath, "r", encoding="utf-8") as f:
        template = f.read()

    # ====================== پردازش {% for %} ======================
    def process_for(match):
        loop_var = match.group(1).strip()
        iterable_name = match.group(2).strip()
        inner = match.group(3)

        # پشتیبانی از enumerate: for i, item in enumerate(items)
        m = re.match(r'^(\w+)\s*,\s*(\w+)\s+in\s+enumerate\((\w+)\)$',
                     f"{loop_var}")
        if not m:
            m = re.match(r'^(\w+)\s*,\s*(\w+)\s+in\s+enumerate\((\w+)\)$',
                         match.group(0).replace('{% for ', '').replace(' %}', '').strip())

        if m and m.group(1) and m.group(2) and m.group(3):
            idx_var = m.group(1)
            item_var = m.group(2)
            iterable_name = m.group(3)
            items = context.get(iterable_name, []) or []
            result = ""
            for idx, item in enumerate(items):
                loop_ctx = context.copy()
                loop_ctx[idx_var] = idx
                loop_ctx[item_var] = item
                result += replace_variables(inner, loop_ctx)
            return result

        # حالت ساده: for item in items
        items = context.get(iterable_name, []) or []
        result = ""
        for item in items:
            loop_ctx = context.copy()
            loop_ctx[loop_var] = item
            result += replace_variables(inner, loop_ctx)
        return result

    template = re.sub(
        r'\{% for\s+(.+?)\s+in\s+(\w+)\s*%\}(.*?)\{% endfor %\}',
        process_for,
        template,
        flags=re.DOTALL
    )

    # ====================== پردازش {% if %} ======================
    # پشتیبانی از if/elif/else/endif (با elif اختیاری)
    def process_if_chain(template_text):
        # ابتدا بلوک‌های if/endif را پیدا کن
        pattern = re.compile(
            r'\{% if\s+(.+?)\s*%\}(.*?)\{% endif %\}',
            re.DOTALL
        )

        def replace_if(match):
            condition = match.group(1).strip()
            body = match.group(2)

            # تقسیم body بر اساس elif و else
            parts = re.split(
                r'\{% elif\s+(.+?)\s*%\}|\{% else\s*%\}',
                body,
                flags=re.DOTALL
            )
            # parts شامل: [if_body, (elif_cond, elif_body), ..., (None, else_body)]
            # ساخت لیست (cond, body)
            branches = []
            branches.append((condition, parts[0]))
            i = 1
            while i < len(parts) - 1:
                elif_cond = parts[i]
                elif_body = parts[i + 1]
                if elif_cond is not None:
                    branches.append((elif_cond, elif_body))
                else:
                    # else
                    branches.append((None, elif_body))
                i += 2

            # ارزیابی شاخه‌ها به ترتیب
            for cond, blk in branches:
                if cond is None:  # else
                    return replace_variables(blk, context)
                if _eval_condition(cond, context):
                    return replace_variables(blk, context)
            return ""

        return pattern.sub(replace_if, template_text)

    # به‌دلیل nesting، چند بار اجرا کن
    prev = None
    while prev != template:
        prev = template
        template = process_if_chain(template)

    # ====================== جایگزینی {{ var }} ======================
    template = replace_variables(template, context)
    return template