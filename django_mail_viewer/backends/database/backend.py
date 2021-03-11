import json
from io import BytesIO
from pathlib import Path

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.mail.backends.base import BaseEmailBackend

from ... import settings as mailviewer_settings


class EmailBackend(BaseEmailBackend):
    """
    An email backend to use during testing and local development with Django Mail Viewer.

    Uses a Django model to store sent emails so that they can be easily retrieved in multi-process environments such as
    using Django Channels or when sending an email from a python shell or for longer term storage and lookup.
    """

    def __init__(self, *args, **kwargs):
        self._backend_model = apps.get_model(mailviewer_settings.MAILVIEWER_DATABASE_BACKEND_MODEL)
        super().__init__(*args, **kwargs)

    def _parse_email_attachment(self, message, decode_file=True):
        """
        Parse an attachment out of an email.message.Message object.

        params:
        msg: email.message.Message object
        decode_file: Boolean whether to decode the base64 encoded file to an actual file or not
        """
        # copied from views.SingleEmailMixin._parse_email_attachment()
        # TODO: deduplicate this. I think it maybe could live on BaseEmailBackend safely
        content_disposition = message.get("Content-Disposition", None)
        if content_disposition:
            dispositions = content_disposition.strip().split(";")
            if bool(content_disposition and dispositions[0].lower() == "attachment"):
                if decode_file:
                    file_data = message.get_payload(decode=True)
                    attachment = BytesIO(file_data)
                    attachment.size = len(file_data)

                    attachment.content_type = message.get_content_type()
                    attachment.name = None
                    attachment.create_date = None
                    attachment.mod_date = None
                    attachment.read_date = None
                else:
                    attachment = None
                for param in dispositions[1:]:
                    name, value = param.split("=")
                    name = name.lower()

                    # Since I am terrible and left terrible comments I am assuming the
                    # datetime TODO comments below mean to store as a datetime.datetime object
                    if name == "filename":
                        attachment.name = value
                    elif name == "create-date":
                        attachment.create_date = value  # TODO: datetime
                    elif name == "modification-date":
                        attachment.mod_date = value  # TODO: datetime
                    elif name == "read-date":
                        attachment.read_date = value  # TODO: datetime
                return {
                    'filename': Path(message.get_filename()).name,
                    'content_type': message.get_content_type(),
                    'file': attachment,
                }
        return None

    def send_messages(self, messages):
        msg_count = 0
        for m in messages:
            # Create db model instances
            message = m.message()
            if message.is_multipart():
                # TODO: Should this really be done recursively? I believe forwarded emails may
                # have multiple layers of parts/dispositions
                message_id = message.get('message-id')
                main_message = None
                for i, part in enumerate(message.walk()):
                    content_type = part.get_content_type()
                    charset = part.get_param('charset')
                    # handle attachments - probably need to look at SingleEmailMixin._parse_email_attachment()
                    # and make that more reusable
                    content_disposition = part.get("Content-Disposition", None)
                    if content_disposition:
                        # attachment_data = part.get_payload(decode=True)
                        attachment_data = self._parse_email_attachment(part)
                        file_attachment = ContentFile(
                            attachment_data.get('file').read(), name=attachment_data.get('filename', 'attachment')
                        )
                        content = ''
                    elif content_type in ['text/plain', 'text/html']:
                        content = part.get_payload(decode=True).decode(charset, errors='replace')
                        file_attachment = ''
                    else:
                        # the main multipart/alternative message for multipart messages has no content/payload
                        # TODO: handle file attachments
                        content = ''
                        file_attachment = ''
                    message_id = part.get('message-id', '')  # do sub-parts have a message-id?
                    p = self._backend_model(
                        message_id=message_id,
                        content=content,
                        file_attachment=file_attachment,
                        parent=main_message,
                        message_headers=json.dumps(dict(part.items())),
                    )
                    p.save()
                    if i == 0:
                        main_message = p
            else:
                message_id = message.get('message-id')
                main_message = self._backend_model(
                    message_id=message_id,
                    content=message.get_payload(),
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
        return self._backend_model.objects.filter(message_id=lookup_id, parent=None).first()

    def get_outbox(self, *args, **kwargs):
        """
        Get the outbox used by this backend.  This backend returns a copy of mail.outbox.
        May add pagination args/kwargs.
        """
        return self._backend_model.objects.filter(parent=None)

    def delete_message(self, message_id: str):
        """
        Remove the message with the given id from the mailbox
        """
        self._backend_model.objects.filter(message_id=message_id).delete()
