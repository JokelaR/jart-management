from django import template

register = template.Library()

@register.filter(name='invert')
def invert(value):
    return not value

@register.filter(name='underscore_to_space')
def underscoreToSpace(value: str):
    return value.replace('_', ' ')