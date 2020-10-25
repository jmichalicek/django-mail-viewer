import email.message.Message
import email.utils.unquote
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


class FileBackedEmailMessageMixin(AbstractBaseEmailMessage):
    """
    Abstract base class for email messages storing emails pickled in a file.
    """

    @cached_property
    def message(self) -> email.message.Message:
        """
        The email.message.Message for this email
        """
        # Does this belong here or on EmailMessage? Perhaps yet another base class should be created for
        # the assumption of a FileField. Another user (or I, in a later version) may want to store this data in a
        # TextField similar to django-pickle-field or may make models to store the entire structure
        # in the database with EmailMessage conforming to email.message.EmailMessage (or Message) API
        with self.serialized_message_file.open('r') as f:
            return pickle.load(f)

    # Stuff to wrap email.message.Message for a partial implementation of that
    # I really only need/use get_filename(), get_content_type(), get_payload(), walk()
    def __str__(self):
        return self.message.__str__()

    def __bytes__(self):
        return self.message.__bytes__()

    def as_string(self, unixfrom=False, maxheaderlen=0, policy=None):
        return self.message.as_string(unixfrom=unixfrom, maxheaderlen=maxheaderlen, policy=policy)

    def as_bytes(self, unixfrom=False, policy=None):
        return self.message.as_bytes(unixfrom=unixfrom, policy=policy)

    def get_content_type(self) -> str:
        """
        Returns the content-type of the email
        """
        return self.message.get_content_type()

    def get_payload(self, decode: bool = False):
        """
        Returns attachment as bytes

        this is from python 3.5 email.message.Message.
        Django still uses email.message.Message rather than email.message.EmailMessage, so going with that.
        """
        return self.message.get_payload(decode=decode)

    def walk(self):
        return self.message.walk()

    def get_filename(self):
        return self.message.get_filename()


# Going with https://stackoverflow.com/a/58756613 for the camel case here vs EMailMessage, etc. because why not?
class FileBackedEmailMessage(FileBackedEmailMessageMixin, AbstractBaseEmailMessage):
    """
    An Email Message where the base message is stored using pickle in a file using your system's default media storage.

    To customize storage, subclass AbstractBaseEmailMessage and add a `FileField()` named `serialized_message_file`
    with the storage you would like to use. This may be because the default media storage is public readable or
    it just needs to be stored elsewhere, such as locally, or a different s3 bucket than the default storage.
    """

    # May likely want a different subclass of
    serialized_message_file = models.FileField(blank=True)


# DB storage implementation idea 2 - entire structure in nested db structure
class EmailMessageQuerySet(models.QuerySet):
    """
    QuerySet to act as a manager which adds methods to automatically defer heavyweight json fields
    """

    def defer_content(self, *args, **kwargs):
        """
        Defers loading of some JSONFields which can be large and greatly increase memory consumption and effect performance
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
    content_type = models.TextField(blank=True, default='')
    # or do I still store this as a FileField()
    content = PickledObjectField(blank=True, default=None)
    message_headers = models.TextField()

    # I really only need/use get_filename(), get_content_type(), get_payload(), walk()

    def is_multipart(self) -> bool:
        return self.content_type == 'rfc/822' or self.parts.all().exists()

    def headers(self):
        return json.loads(self.message_headers)

    def walk(self) -> 'QuerySet[EmailMessage]':
        return self.parts.all()

    def get_payload(self, i: int = None, decode: bool = False):
        """
        Temporary backwards compatibility with email.message.Message
        """
        # TODO: handle decode
        # not sure if I ever even need this, I think when I use this it is
        if self.is_multipart:
            return self.content

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
