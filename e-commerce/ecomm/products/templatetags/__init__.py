from django import template
from .chunks import chunks

register = template.Library()
register.filter('chunks', chunks)