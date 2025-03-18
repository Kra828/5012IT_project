from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    从字典中获取特定键对应的值
    用法: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key) 