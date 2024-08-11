"""
Backend for test environment.
"""

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
        super().__init__(*args, **kwargs)
        if not hasattr(mail, "outbox"):
            mail.outbox = []

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            m = message.message()
            mail.outbox.append(m)
            msg_count += 1
        return msg_count

    def get_message(self, lookup_id):
        """
        Look up and return a specific message in the outbox
        """
        for message in mail.outbox:
            # if a user is manually passing in Message-ID in extra_headers and capitalizing it
            # differently than the expected Message-ID,  which is suppored by
            # EmailMessage.message(), then we can't just access the key directly.  Instead iterate
            # over the keys and vls
            if message.get("message-id") == lookup_id:
                return message
        return None

    def get_outbox(self, *args, **kwargs):
        """
        Get the outbox used by this backend.  This backend returns a copy of mail.outbox.
        May add pagination args/kwargs.
        """
        return getattr(mail, "outbox", [])[:]

    def delete_message(self, message_id: str):
        """
        Remove the message with the given id from the mailbox
        """
        outbox = getattr(mail, "outbox", [])
        index_to_remove = None
        for idx, message in enumerate(outbox):
            if message.get("message-id") == message_id:
                index_to_remove = idx
                break
        if index_to_remove is not None:
            del outbox[index_to_remove]
