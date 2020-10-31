# Not sure I like this. Can I use apps.py to do this a cleaner way?
import json

from django.core.mail.backends.base import BaseEmailBackend

from ... import settings as mailviewer_settings
from .models import EmailMessage


class EmailBackend(BaseEmailBackend):
    """
    An email backend to use during testing and local development with Django Mail Viewer.

    Uses a Django model to store sent emails so that they can be easily retrieved in multi-process environments such as
    using Django Channels or when sending an email from a python shell or for longer term storage and lookup.
    """

    def send_messages(self, messages):
        msg_count = 0
        for m in messages:
            # Create db model instances
            message = m.message()
            if message.is_multipart():
                # TODO: Should this really be done recursively? I believe forwarded emails may
                # have multiple layers of parts/dispositions
                # test this... but this might work
                message_id = message.get('message-id')
                main_message = EmailMessage(
                    message_id=message_id, content=message.get_payload(), content_type=message.get_content_type()
                )
                main_message.save()
                for part in message.walk():
                    content_type = part.get_content_type()
                    charset = part.get_param('charset')
                    if content_type == 'text/plain':
                        # should we get the default charset from the system if no charset?
                        # decode=True handles quoted printable and base64 encoded data
                        # TODO: Suspect this should be decode=False
                        content = part.get_payload(decode=True).decode(charset, errors='replace')
                    elif content_type == 'text/html':
                        # original code set html to '' if it was None and then appended
                        # as if we might have multiple html parts which are just one html message?
                        content = part.get_payload(decode=True).decode(charset, errors='replace')

                    message_id = part.get('message-id', '')  # do sub-parts have a message-id?
                    p = EmailMessage(
                        message_id=message_id,
                        content=content,
                        parent=main_message,
                        content_type=content_type,
                        message_headers=json.dumps(list(part.items())),
                    )
                    p.save()
            else:
                message_id = message.get('message-id')
                main_message = EmailMessage(
                    message_id=message_id,
                    content=message.get_payload(),
                    content_type=message.get_content_type(),
                    message_headers=json.dumps(dict(message.items())),
                )
                main_message.save()

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
        return EmailMessage.objects.filter(message_id=lookup_id).first()

    def get_outbox(self, *args, **kwargs):
        """
        Get the outbox used by this backend.  This backend returns a copy of mail.outbox.
        May add pagination args/kwargs.
        """
        return EmailMessage.objects.all()
