from django.core import mail
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sends an email'

    # def add_arguments(self, parser):
    #     parser.add_argument('to', nargs='+', type=str)
    #     parser.add_argument('cc', nargs='+', type=str)
    #     parser.add_argument('bcc', nargs='+', type=str)
    #     parser.add_argument('file_attachment', nargs='+', type=str)
    #     parser.add_argument('text-only', type=bool)

    def handle(self, *args, **options):
        # Todo, send an html email
        # send_mail(
        #     'Subject here', 'Here is the message.', 'from@example.com', ['to@example.com'], fail_silently=False,
        # )

        m = mail.EmailMultiAlternatives(
            'Subject here', 'The message in text/plain', 'test@example.com', ['to@example.com']
        )
        m.attach_alternative(
            '<html><body><p style="background-color: #AABBFF; color: white">The message as text/html</p></body></html>',
            'text/html',
        )
        m.send()
