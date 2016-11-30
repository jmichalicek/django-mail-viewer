"""
Backend for test environment.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    """
    An email backend to use during testing and local development with Django Mail Viewer.

    Similar to django.core.backends.locmem.EmailBackend, this adds an outbox attribute ot
    django.core.mail.  This stores the EmailMessage object as well as message.message().
    This is because many of the headers are generated at the time message.message() is called
    and are not stored by the default locmem backend, including ones useful for consistently
    looking up a specific message even if the list is reordered.
    """

    def __init__(self, *args, **kwargs):
        super(EmailBackend, self).__init__(*args, **kwargs)
        if not hasattr(mail, 'outbox'):
            mail.outbox = []

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            m = message.message()
            lookup_id = m.get('Message-ID').strip('<>')
            mail.outbox.append((lookup_id, message, m))
            msg_count += 1
        return msg_count

    def get_message(self, lookup_id):
        for message in mail.outbox:
            if message[0] == lookup_id:
                return message
        return None

