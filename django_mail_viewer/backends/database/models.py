import email.message
import email.utils
import json
from typing import TYPE_CHECKING, Any, Dict, List, Union

from django.db import models


class AbstractBaseEmailMessage(models.Model):
    """
    Abstract base class for email messages allowing users to easily make their own class with a custom
    storage for the Message FileField. Once Django 3.1+ only is supported then a callable may be used
    rendering this not really necessary.

    To customize, subclass this and add a `FileField()` named `serialized_message_file` with the storage you would
    like to use.
    """

    # Technically optional, but really should be there according to RFC 5322 section 3.6.4
    # and Django always creates the message_id on the main part of the message so we know
    # it will be there, but not for all sub-parts of a multi-part message
    message_id = models.CharField(max_length=250, blank=True, default='')
    # Would love to make message_headers be a JSONField, but do not want to tie this to
    # postgres only.
    message_headers = models.TextField()
    content = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self', blank=True, null=True, default=None, related_name='parts', on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # methods here expect the concrete subclasses to implement the file_attachment field
        # should only be necessary until django 2.2 support is dropped... I hope
        if TYPE_CHECKING and not hasattr(self, 'file_attachment'):
            self.file_attachment = models.FileField(blank=True, default='', upload_to='mailviewer_attachments')

    # I really only need/use get_filename(), get_content_type(), get_payload(), walk()
    # returns Any due to failobj
    def get(self, attr: str, failobj: Any = None) -> Any:
        """
        Get a header value.

        Like __getitem__() but return failobj instead of None when the field
        is missing.
        """
        # Or should I muck with __getitem__ and __setitem__, etc
        # like in https://github.com/python/cpython/blob/3.8/Lib/email/message.py#L382
        vals = {k.lower(): v for k, v in self.headers().items()}
        if vals:
            lower_attr = attr.lower()
            return vals.get(lower_attr, failobj)
        return failobj

    def date(self) -> str:
        return self.get('date')

    def is_multipart(self) -> bool:
        """
        Returns True if the message is multipart
        """
        # Not certain the self.parts.all() is accurate
        return self.get_content_type() == 'rfc/822' or self.parts.exists()  # type: ignore

    def headers(self) -> Dict[str, str]:
        """
        Return the Messages email headers as a dict
        """
        return json.loads(self.message_headers)

    def values(self) -> Dict[str, str]:
        """
        Return the Messages email headers as a dict
        """
        # not sure this is right...
        return self.headers()

    def walk(self) -> 'Union[models.QuerySet[AbstractBaseEmailMessage], List[AbstractBaseEmailMessage]]':
        if not self.parts.all().exists():  # type: ignore
            # Or should I be saving a main message all the time and even just a plaintext has a child part, hmm
            return [self]
        return self.parts.all().order_by('-created_at', 'id')  # type: ignore

    def get_param(self, param: str, failobj=None, header: str = 'content-type', unquote: bool = True) -> str:
        """
        Return the value of the Content-Type header’s parameter param as a string. If the message has no Content-Type header or if there is no such parameter, then failobj is returned (defaults to None).

        Optional header if given, specifies the message header to use instead of Content-Type.
        See https://docs.python.org/3/library/email.compat32-message.html#email.message.Message.get_param
        """
        # TODO: error handling skipped for sure here... need to see what the real email message does
        # Should also consider using cgi.parse_header
        h = self.get(header)
        params = h.split(';')
        for part in params[1:]:
            part_name, part_val = part.split('=')
            part_name = part_name.strip()
            part_val = part_val.strip()
            if part_name == param:
                return part_val
        return ''

    def get_payload(
        self, i: Union[int, None] = None, decode: bool = False
    ) -> 'Union[bytes, AbstractBaseEmailMessage, models.QuerySet[AbstractBaseEmailMessage]]':
        """
        Temporary backwards compatibility with email.message.Message
        """
        # TODO: sort out type hint for return value here. Maybe use monkeytype to figure this out.
        if not self.is_multipart():
            charset = self.get_param('charset')
            if self.file_attachment:
                self.file_attachment.seek(0)
                try:
                    return self.file_attachment.read()
                finally:
                    self.file_attachment.seek(0)
            else:
                # our content is a str but get_payload() returns bytes normally so we need to re-encode it... yeah.
                return self.content.encode(charset)

        parts = self.parts.all()  # type: ignore
        if i:
            return parts[i]
        return parts

    def get_content_type(self) -> str:
        """
        Return's the message's content-type or mime type.
        """
        h = self.get('content-type')
        params = h.split(';')
        return params[0]

    def get_filename(self, failobj=None) -> str:
        content_disposition = self.headers().get('Content-Disposition', '')
        parts = content_disposition.split(';')
        for part in parts:
            if part.strip().startswith('filename'):
                filename = part.split('=')[1].strip('"').strip()
                return email.utils.unquote(filename)
        return ''


class EmailMessage(AbstractBaseEmailMessage):
    """
    Django model mimicking the minimal implementation of email.message.Message needed for django-mail-viewer.

    An Email Message where the base message is stored in the database and attachments are stored in a `mailviewer_attachments/
    directory in your default media storage.

    To customize storage, subclass AbstractBaseEmailMessage and add a `FileField()` named `file_attachment`
    with the storage you would like to use. This may be because the default media storage is public readable or
    it just needs to be stored elsewhere, such as locally, or a different s3 bucket than the default storage.
    """

    file_attachment = models.FileField(blank=True, default='', upload_to='mailviewer_attachments')

    class Meta:
        db_table = 'mail_viewer_emailmessage'
        ordering = ('id',)
        indexes = [models.Index(fields=['message_id'])]
