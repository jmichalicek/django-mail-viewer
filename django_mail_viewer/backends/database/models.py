from django.db import models
from django.core.mail.backends.base import BaseEmailBackend
import email.message.Message
from typing import Tuple


# Going with https://stackoverflow.com/a/58756613 for the camel case here vs EMailMessage, etc. because why not?
class EmailMessage(models.Model):
    """
    An Email Message
    """

    # Should this be the pk? Technically optional, but really should be there according to RFC 5322 section 3.6.4
    message_id = models.CharField(max_length=250, blank=True, default='')
    # TextField for all of these because RFC 5322 basically says there is no max length.
    # It states max 998 chars/bytes per line but subject, etc. can be multiple lines
    # https://tools.ietf.org/html/rfc5322#section-2.1.1
    subject = models.TextField(max_length=500, blank=True, default='')
    sender = models.TextField(max_length=500, blank=True, default='')
    # very tempting to use an ArrayField for cc and bcc, but then this becomes postgres specific
    to = models.TextField(blank=True, default='')
    cc = models.TextField(blank=True, default='')
    bcc = models.TextField(blank=True, default='')
    sent_on = models.DateTimeField(blank=True, null=True, default=None)

    # Valid max length? should it be longer or be a TextField?
    content_type = models.CharField(max_length=250, blank=True, default='')

    text_body = models.TextField(blank=True, default='')
    # Technically an attachment, but treat it special
    html_body = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Maybe pointless but some indexes for easily searching/filtering.
        indexes = [
            models.Index(fields=['message_id',]),
            models.Index(fields=['to',]),
            models.Index(fields=['cc',]),
            models.Index(fields=['bcc',]),
        ]

    def __str__(self):
        return self.message_id  # or return subject? or pk?

    def get_email_parts(self) -> Tuple[str, str, str, str, str]:
        """
        Returns the different parts of the email - this is replacing  SingleEmailMixin._parse_email_parts()

        Not sure about best way to handle attachments yet - I do not really want to load them all up. Perhaps
        I will remove attachments and handle that separately

        Returns: (subject, body, html, msg_from, to, attachments)
        """
        return (self.subject, self.text_body, self.html_body, self.sender, self.to, [])

    def as_email_message(self) -> email.message.Message:
        """
        Converts the data to a email.message.Message
        """
        pass


class EmailAttachment(models.Model):
    """
    A file attachment for an email
    """

    email_message = models.ForeignKey(EmailMessage)
    attachment_file = models.FileField(blank=True, default='')
    # The file storage backend may muck with the filename, so store the original filename
    filename = models.CharField(max_length=500, blank=True, default='')
    content_type = models.CharField(max_length=250, blank=True, default='')

    def __str__(self) -> str:
        return 'Attachment for %s' % self.email_message
