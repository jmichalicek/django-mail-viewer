from __future__ import unicode_literals, absolute_import, division, print_function

from django.core import mail
from django.http import Http404, HttpResponse
from django.utils.encoding import smart_str
from django.views.generic.base import TemplateView, View

import os


class EmailListView(TemplateView):
    """
    Display a list of sent emails.
    """
    template_name = 'mail_viewer/email_list.html'

    def get_context_data(self, **kwargs):
        # TODO: need to make a custom backend which sets a predictable message-id header.
        # built in locmem uses a random number each time the message is accessed
        # preventing lookup in the detail view
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            if hasattr(mail, 'outbox'):
                # TODO: remove this
                mail.outbox = []
                ### TEMP FAKE STUFF JUST TO SEE IT WORK

                mail.send_mail(
                        "testing subject",
                        "Hey there!",
                        "test@example.com",
                        ['to1@example.com', 'to2.example.com'],
                        html_message='<html><body>Hey, there HTML!</body></html>',
                        connection=connection)

                m = mail.EmailMultiAlternatives('HTML Mail Subject', 'html email text', 'test@example.com',
                        ['to1@example.com', 'to2.example.com'],
                        connection=connection)
                m.attach_alternative('<html><body><p style="background-color: AABBFF; color: white">HTML Email Content</p></body></html>', 'text/html')
                current_dir = os.path.dirname(__file__)
                test_file_attachment = os.path.join(current_dir, 'icon_e_confused.gif')
                m.attach_file(test_file_attachment)
                m.send()
                # TODO: attachment
                #### END
                # locmem backend
                outbox  = mail.outbox[:]
        return super(EmailListView, self).get_context_data(outbox=outbox, **kwargs)


class EmailDetailView(TemplateView):
    """
    Display details of an email
    """
    template_name = 'mail_viewer/email_detail.html'

    def get_message(self):
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            message_id = self.kwargs.get('message_id')
            message = connection.get_message(message_id)
            if message:
                return message
        raise Http404('Message id not found')

    def get_context_data(self, **kwargs):
        lookup_id, message, headers = self.get_message()

        text_body = message.body.strip()
        html_body = None
        for alternative in message.alternatives:
            if alternative[1].lower() == 'text/html':
                html_body = alternative[0].strip()
                break
        return super(EmailDetailView, self).get_context_data(lookup_id=lookup_id,
                                                             message=message,
                                                             text_body=text_body,
                                                             html_body=html_body,
                                                             headers=headers,
                                                             attachments=message.attachments,
                                                             **kwargs)

class EmailAttachmentDownloadView(View):
    """
    Stream out an email attachment to the web browser
    """

    def get_message(self):
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            message_id = self.kwargs.get('message_id')
            message = connection.get_message(message_id)
            if message:
                return message
        raise Http404('Message id not found')
    
    def get_attachment(self, message):
        # TODO: eventually will need to handle different ways of having these
        # attachments stored.  Probably handle that on the EmailBackend class
        try:
            return message.attachments[int(self.kwargs.get('attachment'))]
        except IndexError:
            raise Http404('Attachment not found')

    def get(self, request, *args, **kwargs):
        lookup_id, message, headers = self.get_message()
        attachment = self.get_attachment(message) 
        response = HttpResponse(attachment[1], content_type=attachment[2])
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(attachment[0])
        return response
