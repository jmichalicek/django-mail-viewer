from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail


class Command(BaseCommand):
    help = 'Sends an email'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        # Todo, send an html email
        send_mail(
            'Subject here', 'Here is the message.', 'from@example.com', ['to@example.com'], fail_silently=False,
        )
