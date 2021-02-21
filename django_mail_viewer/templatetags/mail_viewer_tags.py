from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def message_attribute(message, attribute):
    """
    Return the attribute from the SafeMIMEMessage

    This is required to deal with case insensitivity and some attributes use
    a hyphen in the name.  In a template, message.message-id, for example does
    not work due to the hyphen.
    """
    return message.get(attribute)


@register.simple_tag
def message_lookup_id(message):
    """
    Return the message id of an email message.

    Useful because the value is stored in a dict with a hyphen in the key,
    making it inaccessible directly.
    """

    return mark_safe(message.get('message-id', '').strip('<>'))


@register.simple_tag
def display_message_attribute(message, attribute):
    return mark_safe(message_attribute(message, attribute))
