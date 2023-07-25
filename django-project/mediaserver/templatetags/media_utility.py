from django import template

register = template.Library()

@register.filter(name='invert')
def invert(value):
    return not value