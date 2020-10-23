from django.core.mail.backends.base import BaseEmailBackend

from ... import settings as mailviewer_settings

# Not sure I like this. Can I use apps.py to do this a cleaner way?
from .models import EmailMessage


class EmailBackend(BaseEmailBackend):
    """
    An email backend to use during testing and local development with Django Mail Viewer.

    Uses a Django model to store sent emails so that they can be easily retrieved in multi-process environments such as
    using Django Channels or when sending an email from a python shell or for longer term storage and lookup.
    """

    def send_messages(self, messages):
        msg_count = 0
        for message in messages:
            # Create db model instances
            m = message.message()
            message_id = m.get('message-id')
            subject = m.get('subject')
            sender = m.get('from')
            to = m.get('to')
            e = EmailMessage(message_id=message_id, subject=subject, to=to, sender=sender)
            e.save()

            msg_count += 1
        return msg_count

    def get_message(self, lookup_id):
        """
        Look up and return a specific message in the outbox
        """
        # Should this look at the db model and turn these into email.message.Message objects?
        # or should the views be updated so that more of their logic lives in the EmailBackend?
        # or should there be a layer in between or some sort of adapter pattern to make the db based email message
        # look/act like an email.message.Message? I lean towards just moving logic to the EmailBackend but may need
        # some combo of the two for the views/templates to work nicely.
        pass

    def get_outbox(self, *args, **kwargs):
        """
        Get the outbox used by this backend.  This backend returns a copy of mail.outbox.
        May add pagination args/kwargs.
        """
        pass
        # Query db for EmailMessage instance(s)
