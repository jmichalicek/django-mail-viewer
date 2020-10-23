from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DatabaseBackendConfig(AppConfig):
    name = 'django_mail_viewer.database_backend'
    # May want to change this verbose_name
    verbose_name = _("Database Backend")
