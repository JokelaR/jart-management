from django import template

register = template.Library()

@register.filter(name='invert')
def invert(value):
    return not value

@register.filter(name='underscore_to_space')
def underscoreToSpace(value: str):
    return value.replace('_', ' ').lstrip('0123456789 ')

@register.simple_tag(name='image_size')
def image_size(width: int, height: int) -> str:
    max_width = 966

    ratio = width / height
    width = min(width, max_width)
    new_height = width / ratio

    return f'height={new_height} width={width}'