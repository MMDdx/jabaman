# template_engine.py
"""موتور قالب اختصاصی سبک Jinja2.

تغییرات نسبت به نسخه‌ی قبل:
- HTML escaping خودکار برای جلوگیری از XSS.
- پشتیبانی از sqlite3.Row (نه فقط dict).
- پشتیبانی از فیلتر length: {{ list|length }}.
- پشتیبانی از شرط‌های مقایسه‌ای: {% if var == 'value' %} و {% if not var %}.
- پشتیبانی از حلقه با اندیس {% for i, item in enumerate(items) %}.
- قابلیت{% elif %} و {% else %} در if.
- **اصلاح باگ مهم:** پشتیبانی صحیح از if/else و for تو در تو (nested)
  با استفاده از پارسر بازگشتی به‌جای regex.
"""
import re
import html
import os
from collections.abc import Mapping

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# الگوی پیدا‌ کردن همه‌ی تگ‌های {%%}
_TAG_PATTERN = re.compile(
    r'\{%\s*(if|elif|else|endif|for|endfor)\s*([^%]*?)\s*%\}',
    re.DOTALL
)


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
    - فیلتر safe: {{ var|safe }} (در replace_variables هندل می‌شود)
    """
    expr = expr.strip()

    # فیلتر length یا safe
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
        # فیلترهای دیگر (از جمله safe که در replace_variables هندل می‌شود)
        return str(val) if val is not None else ""

    # دسترسی با نقطه
    if "." in expr:
        parts = expr.split(".")
        obj = context.get(parts[0])
        for part in parts[1:]:
            if obj is None or obj == "":
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
        elif right_raw.lstrip('-').isdigit():
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


# ============================================================
#   پارسر بازگشتی (Tokenizer → AST → Renderer)
# ============================================================
#
#   موتور قدیمی با regex کار می‌کرد که در حالت if/for تو در تو
#   باگ داشت (باگ نمایش علاقه‌مندی‌ها). این نسخه‌ی جدید از یک
#   پارسر بازگشتی استفاده می‌کند که درست با nesting رفتار می‌کند.
#


def _tokenize(template):
    """تجزیه‌ی قالب به لیست توکن‌ها.

    هر توکن یک تاپل (type, value) است:
    - ('text', str)             متن ساده
    - ('if', condition_str)     {% if cond %}
    - ('elif', condition_str)   {% elif cond %}
    - ('else', '')              {% else %}
    - ('endif', '')             {% endif %}
    - ('for', header_str)       {% for ... %}
    - ('endfor', '')            {% endfor %}
    """
    tokens = []
    pos = 0
    for m in _TAG_PATTERN.finditer(template):
        if m.start() > pos:
            tokens.append(('text', template[pos:m.start()]))
        tag = m.group(1)
        arg = m.group(2).strip() if m.group(2) else ''
        tokens.append((tag, arg))
        pos = m.end()
    if pos < len(template):
        tokens.append(('text', template[pos:]))
    return tokens


def _parse_nodes(tokens, i, stop_tags):
    """پارس لیست توکن‌ها تا رسیدن به یک تگ stop.

    ورودی:
      tokens       : لیست توکن‌ها
      i            : اندیس شروع
      stop_tags    : set از tagهایی که باید در برخورد با آن‌ها توقف کنیم

    خروجی:
      (nodes, next_i) که nodes لیست ندهای AST و next_i اندیس توکنی
      است که باعث توقف شده (هنوز مصرف نشده).
    """
    nodes = []
    while i < len(tokens):
        tag, arg = tokens[i]
        if tag in stop_tags:
            return nodes, i
        elif tag == 'text':
            nodes.append(('text', arg))
            i += 1
        elif tag == 'if':
            branches, next_i = _parse_if(tokens, i)
            nodes.append(('if', branches))
            i = next_i
        elif tag == 'for':
            body, next_i = _parse_for(tokens, i)
            nodes.append(('for', arg, body))
            i = next_i
        else:
            # تگ غیرمنتظره (elif/else/endif/endfor بدون جفت) → رد کن
            i += 1
    return nodes, i


def _parse_if(tokens, i):
    """پارس یک بلوک if شروع‌شده در tokens[i].

    خروجی: (branches, next_i)
      branches = لیست (condition, body_nodes). condition == None برای else.
    """
    if_cond = tokens[i][1]  # شرط if
    i += 1

    branches = []
    body_nodes, i = _parse_nodes(tokens, i, {'elif', 'else', 'endif'})
    branches.append((if_cond, body_nodes))

    while i < len(tokens):
        tag, arg = tokens[i]
        if tag == 'elif':
            i += 1
            body_nodes, i = _parse_nodes(tokens, i, {'elif', 'else', 'endif'})
            branches.append((arg, body_nodes))
        elif tag == 'else':
            i += 1
            body_nodes, i = _parse_nodes(tokens, i, {'elif', 'else', 'endif'})
            branches.append((None, body_nodes))
        elif tag == 'endif':
            i += 1  # مصرف endif
            return branches, i
        else:
            # نباید اینجا برسد
            return branches, i
    return branches, i


def _parse_for(tokens, i):
    """پارس یک بلوک for شروع‌شده در tokens[i].

    خروجی: (body_nodes, next_i)
    """
    i += 1  # مصرف for
    body_nodes, i = _parse_nodes(tokens, i, {'endfor'})
    if i < len(tokens) and tokens[i][0] == 'endfor':
        i += 1  # مصرف endfor
    return body_nodes, i


def _render_for(header, body_nodes, context):
    """رندر یک حلقه‌ی for.

    header می‌تواند یکی از این دو حالت باشد:
      - "item in items"
      - "i, item in enumerate(items)"
    """
    # حالت enumerate
    m = re.match(
        r'^(\w+)\s*,\s*(\w+)\s+in\s+enumerate\((\w+)\)$',
        header.strip()
    )
    if m:
        idx_var = m.group(1)
        item_var = m.group(2)
        iterable_name = m.group(3)
        items = context.get(iterable_name) or []
        result = []
        for idx, item in enumerate(items):
            loop_ctx = context.copy()
            loop_ctx[idx_var] = idx
            loop_ctx[item_var] = item
            result.append(_render_nodes(body_nodes, loop_ctx))
        return ''.join(result)

    # حالت ساده
    m = re.match(r'^(\w+)\s+in\s+(\w+)$', header.strip())
    if m:
        item_var = m.group(1)
        iterable_name = m.group(2)
        items = context.get(iterable_name) or []
        result = []
        for item in items:
            loop_ctx = context.copy()
            loop_ctx[item_var] = item
            result.append(_render_nodes(body_nodes, loop_ctx))
        return ''.join(result)

    # هدر نامعتبر
    return ''


def _render_nodes(nodes, context):
    """رندر لیست ندهای AST با context داده‌شده.

    - برای متن: replace_variables (شامل {{ }}) اعمال می‌شود.
    - برای if: شاخه‌ی درست انتخاب و بازگشتی رندر می‌شود.
    - برای for: تکرار روی آیتم‌ها و رندر بازگشتی بدنه.
    """
    result = []
    for node in nodes:
        if node[0] == 'text':
            result.append(replace_variables(node[1], context))
        elif node[0] == 'if':
            branches = node[1]
            chosen = None
            for cond, body in branches:
                if cond is None:  # else
                    chosen = body
                    break
                if _eval_condition(cond, context):
                    chosen = body
                    break
            if chosen is not None:
                result.append(_render_nodes(chosen, context))
        elif node[0] == 'for':
            header = node[1]
            body = node[2]
            result.append(_render_for(header, body, context))
    return ''.join(result)


def render_template(template_name, context=None):
    """رندر یک قالب با context داده‌شده.

    از autoescape به‌صورت پیش‌فرض استفاده می‌شود.
    برای محتوای trusted می‌توان از فیلتر |safe استفاده کرد.

    پیاده‌سازی با پارسر بازگشتی که درست با if/for تو در تو کار می‌کند.
    """
    if context is None:
        context = {}

    filepath = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(filepath):
        return f"Template {template_name} not found."

    with open(filepath, "r", encoding="utf-8") as f:
        template = f.read()

    tokens = _tokenize(template)
    nodes, _ = _parse_nodes(tokens, 0, set())
    return _render_nodes(nodes, context)
