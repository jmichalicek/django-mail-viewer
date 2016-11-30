from __future__ import unicode_literals, absolute_import, division, print_function

from django.core import mail
from django.http import Http404
from django.views.generic.base import TemplateView

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
                m.attach_alternative('<html><body><p>HTML Email Content</p></body></html>', 'text/html')
                current_dir = os.path.dirname(__file__)
                test_file_attachment = os.path.join(current_dir, 'icon_e_confused.gif')
                m.attach('design.png', test_file_attachment, 'image/png')
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
        return super(EmailDetailView, self).get_context_data(lookup_id=lookup_id,
                                                             message=message,
                                                             headers=headers,
                                                             **kwargs)

