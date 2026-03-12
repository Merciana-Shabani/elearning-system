from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    """Return d[key] for use in templates (e.g. my_grades|get_item:item.pk)."""
    if d is None:
        return None
    return d.get(key)
