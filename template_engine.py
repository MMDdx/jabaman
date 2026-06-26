import re
import os

TEMPLATE_DIR = "templates"

def render_template(template_name, context=None):
    if context is None:
        context = {}

    filepath = os.path.join(TEMPLATE_DIR, template_name)
    if not os.path.exists(filepath):
        return f"Template {template_name} not found."

    with open(filepath, "r", encoding="utf-8") as f:
        template = f.read()

    # پردازش حلقه‌های {% for item in items %} ... {% endfor %}
    def process_for(match):
        loop_var = match.group(1).strip()
        iterable_name = match.group(2).strip()
        inner = match.group(3)
        items = context.get(iterable_name, [])
        result = ""
        for item in items:
            loop_ctx = context.copy()
            loop_ctx[loop_var] = item
            result += replace_variables(inner, loop_ctx)
        return result

    template = re.sub(
        r'\{% for (\w+) in (\w+) %\}(.*?)\{% endfor %\}',
        process_for,
        template,
        flags=re.DOTALL
    )

    # پردازش شرط‌های {% if var %} ... {% endif %}
    def process_if(match):
        var = match.group(1).strip()
        true_block = match.group(2)
        false_block = match.group(3) if match.group(3) else ""
        if context.get(var):
            return replace_variables(true_block, context)
        else:
            return replace_variables(false_block, context)

    template = re.sub(
        r'\{% if (\w+) %\}(.*?)(?:\{% else %\}(.*?))?\{% endif %\}',
        process_if,
        template,
        flags=re.DOTALL
    )

    # جایگزینی {{ var }}
    template = replace_variables(template, context)
    return template

def replace_variables(text, context):
    def replacer(match):
        key_expr = match.group(1).strip()
        # پشتیبانی از دسترسی با نقطه: prop.title
        if '.' in key_expr:
            parts = key_expr.split('.', 1)
            obj = context.get(parts[0])
            if isinstance(obj, dict):
                val = obj.get(parts[1], "")
            else:
                val = ""
            return str(val) if val is not None else ""
        # حالت عادی: {{ variable }}
        value = context.get(key_expr, "")
        return str(value) if value is not None else ""
    return re.sub(r'\{\{ (.*?) \}\}', replacer, text)