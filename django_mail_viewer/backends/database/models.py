import email.message
import email.utils
import json
import pickle
from email.charset import Charset
from typing import Tuple

from django.core.mail.backends.base import BaseEmailBackend
from django.db import models
from django.utils.functional import cached_property

from picklefield.fields import PickledObjectField


class AbstractBaseEmailMessage(models.Model):
    """
    Abstract base class for email messages allowing users to easily make their own class with a custom
    storage for the Message FileField. Once Django 3.1+ only is supported then a callable may be used
    rendering this not really necessary.

    To customize, subclass this and add a `FileField()` named `serialized_message_file` with the storage you would
    like to use.
    """

    # Should this be the pk? Technically optional, but really should be there according to RFC 5322 section 3.6.4
    message_id = models.CharField(max_length=250, blank=True, default='', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# DB storage implementation idea 2 - entire structure in nested db structure
class EmailMessageQuerySet(models.QuerySet):
    """
    QuerySet to act as a manager which adds methods to automatically defer heavyweight json fields
    """

    def defer_content(self, *args, **kwargs):
        """
        Defers loading of some content PickledObjectField which can be large and greatly increase memory consumption and effect performance
        """
        return self.defer('content',)


class EmailMessage(AbstractBaseEmailMessage):
    """
    Django model mimicking the minimal implementation of email.message.Message needed for django-mail-viewer
    Django still uses email.message.Message rather than email.message.EmailMessage, so going with that.
    """

    objects = EmailMessageQuerySet.as_manager()

    parent = models.ForeignKey(
        'self', blank=True, null=True, default=None, related_name='parts', on_delete=models.CASCADE
    )
    # TODO: I do not think I actually need this, I can just grab it from the headers
    content_type = models.TextField(blank=True, default='')
    # or do I still store this as a FileField()
    content = PickledObjectField(blank=True, default=None)
    message_headers = models.TextField()

    class Meta:
        db_table = 'mail_viewer_emailmessage'

    # I really only need/use get_filename(), get_content_type(), get_payload(), walk()

    def get(self, attr, failobj=None):
        """Get a header value.
        Like __getitem__() but return failobj instead of None when the field
        is missing.
        """
        # Or should I muck with __getitem__ and __setitem__, etc
        # like in https://github.com/python/cpython/blob/3.8/Lib/email/message.py#L382
        vals = {k.lower(): v for k, v in self.values().items()}
        if vals:
            lower_attr = attr.lower()
            return vals.get(lower_attr, failobj)
        return failobj

    def is_multipart(self) -> bool:
        # Not certain the self.parts.all() is accurate
        return self.content_type == 'rfc/822' or self.parts.all().exists()

    def headers(self):
        return json.loads(self.message_headers)

    def values(self):
        return self.headers()

    def walk(self) -> 'QuerySet[EmailMessage]':
        if not self.parts.all().exists():
            # Or should I be saving a main message all the time and even just a plaintext has a child part, hmm
            return [self]
        return self.parts.all()

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

    def get_payload(self, i: int = None, decode: bool = False):
        """
        Temporary backwards compatibility with email.message.Message
        """
        # TODO: handle decode

        # TODO: This seems wrong....
        if not self.is_multipart():
            charset = self.get_param('charset')
            # our content is a str but get_payload() returns bytes normally so we need to re-encode it... yeah.
            # not certain always going utf-8 is smart here, but it's what I am doing for now.
            return self.content.encode(charset)

        parts = self.parts.all()
        if i:
            return parts[i]
        return parts

    def get_content_type(self):
        return self.content_type

    def get_filename(self, failobj=None):
        content_disposition = self.headers.get('content_disposition', '')
        parts = content_disposition.split(';')
        for part in parts:
            if part.strip().startswith('filename'):
                filename = part.split('=')[:1].strip('"').strip()
                return email.utils.unquote(filename)
        return ''