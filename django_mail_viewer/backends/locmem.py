"""
Backend for test environment.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.utils import six


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
        # TODO: Tweak this.  If the same message object is used to multiple times it will get put in the mailbox twice
        # but identifying which send will not be reasonable.  We also make use of headers which are calculated
        # at runtime in EmailMessage.message() and so are not accurate when displayed.  We need to have mail.outbox
        # store both the EmailMessage instance AND the dict returned by EmailMessage.message() perhaps as a list of tuples.
        msg_count = 0
        for message in messages:
            m = message.message()
            lookup_id = m.get('Message-ID').strip(u'<>')
            mail.outbox.append((message, m))
            msg_count += 1
        return msg_count

    def get_message(self, lookup_id):
        for message in mail.outbox:
            # if a user is manually passing in Message-ID in extra_headers and capitalizing it
            # differently than the expected Message-ID,  which is suppored by
            # EmailMessage.message(), then we can't just access the key directly.  Instead iterate
            # over the keys and vls
            if message[1].get('message-id') == '<%s>' % lookup_id:
                return message
            #for k, v in six.iteritems(message[1]):
            #    if k.lower() == 'message-id' and '<%s>' % v  == lookup_id:
            #        return message
        return None

