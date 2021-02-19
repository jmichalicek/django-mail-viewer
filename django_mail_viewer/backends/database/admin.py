from django.contrib import admin

from .models import EmailMessage


class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'parent', 'message_id', 'created_at', 'updated_at')
    search_fields = ('pk', 'message_id', 'message_headers')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(EmailMessage, EmailMessageAdmin)
