"""
Backend for test environment.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    """
    An email backend to use during testing and local development with Django Mail Viewer.

    Mirrors django.core.backends.locmem.EmailBackend to set a consistent Message-ID header
    on each email so that a single email can easily be retrieved/viewed.  This is done by
    adding the 'Message-ID' key to `extra_headers` if it is not already there.
    """

    def __init__(self, *args, **kwargs):
        super(EmailBackend, self).__init__(*args, **kwargs)
        if not hasattr(mail, 'outbox'):
            mail.outbox = []

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            header_names = [key.lower() for key in message.extra_headers]
            m = message.message()
            if 'message-id' not in header_names:
                message.extra_headers['Message-ID'] = m['Message-ID']
            mail.outbox.append(message)
            print('extra headers is %s' % message.extra_headers)
            msg_count += 1
        return msg_count
