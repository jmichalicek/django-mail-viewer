from __future__ import absolute_import, unicode_literals, print_function, division

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def email_message_id(message):
    """
    Return the message id of an email message.

    Useful because the value is stored in a dict with a hyphen in the key,
    making it inaccessible directly.
    """

    return mark_safe(message.message().get('message-id', ''))
