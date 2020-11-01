from django.contrib import admin
from .models import EmailMessage


class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'parent', 'message_id', 'created_at', 'updated_at')
    search_fields = ('pk', 'message_id', 'message_headers')
    # TODO: conditionally include content field? Don't really want to show it if it's a 2GB file attachment...
    # Using a FileField here would solve that as well, then while not directly viewable, it could be easily made
    # downloadable
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(EmailMessage, EmailMessageAdmin)
