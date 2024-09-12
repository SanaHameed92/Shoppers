from django import template

register = template.Library()

@register.filter(name='chunks')
@register.filter(name='chunks')
def chunks(list_data, chunk_size):
    return [list_data[i:i + chunk_size] for i in range(0, len(list_data), chunk_size)]
