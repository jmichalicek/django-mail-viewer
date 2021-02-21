from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DatabaseBackendConfig(AppConfig):
    label = 'mail_viewer_database_backend'
    name = 'django_mail_viewer.backends.database'
    # May want to change this verbose_name
    verbose_name = _("Database Backend")
