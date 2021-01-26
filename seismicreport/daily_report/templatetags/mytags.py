from django import template

register = template.Library()

@register.filter
def f_format(value, format_str):
    if value:
        try:
            return f'{value:{format_str}}'

        except ValueError:
            return value

    else:
        return value
