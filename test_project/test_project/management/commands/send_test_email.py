from django.core import mail
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

import magic


class Command(BaseCommand):
    help = "Sends an email"

    def add_arguments(self, parser):
        #     parser.add_argument('to', nargs='+', type=str)
        #     parser.add_argument('cc', nargs='+', type=str)
        #     parser.add_argument('bcc', nargs='+', type=str)
        #     parser.add_argument('text-only', type=bool)
        parser.add_argument("-a", "--attach-file", nargs="?", type=str, required=False)

    def handle(self, *args, **options):
        m = mail.EmailMultiAlternatives(
            "Subject here", "The message in text/plain", "test@example.com", ["to@example.com"]
        )
        m.attach_alternative(
            "<html><head>"
            "<style>"
            "@font-face {font-family: SourceCodePro; src: url(/static/fonts/SourceCodePro-Light.otf);}"
            "</style>"
            '</head><body><p style="font-family: SourceCodePro; background-color: #AABBFF; color: white">The message as text/html</p></body></html>',
            "text/html",
        )
        attach_file = options.get("attach_file", "")
        if attach_file:
            mime_type = magic.from_file(attach_file, mime=True)
            m.attach_file(attach_file, mime_type)
        m.send()
