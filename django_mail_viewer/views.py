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
            elif hasattr(connection, 'file_path'):
                # filebased backend
                # read the files, make list, return it?  Will need to experiment with backend
                # to see how it stores html email, attachments, etc.
                raise ValueError("Only the locmem email backend is currently supported")
            else:
                # raise exception about unsupport backend?
                raise ValueError("Only the locmem email backend is currently supported")
        return super(EmailListView, self).get_context_data(outbox=outbox, **kwargs)


class EmailDetailView(TemplateView):
    """
    Display details of an email
    """
    template_name = 'mail_viewer/email_detail.html'

    def get_message(self):
        with mail.get_connection('django_mail_viewer.backends.locmem.EmailBackend') as connection:
            # TODO: possibly move this logic to a method on the EmailBackend, allowing for easier implementation
            # of multiple EmailBackends which look up/store the data differently.
            for message in mail.outbox:
                message_id = message.message()['Message-ID']
                if message_id == '<%s>' % self.kwargs.get('message_id'):
                    return message
        raise Http404('Message id not found')

    def get_context_data(self, **kwargs):
        message = self.get_message()
        return super(EmailDetailView, self).get_context_data(message=message, **kwargs)

