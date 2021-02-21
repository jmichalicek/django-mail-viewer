from django.conf import settings

# The cache config from django.core.cache.caches to use for backends.cache.CacheBackend
# default to django.core.cache.caches['default']
MAILVIEWER_CACHE = getattr(settings, 'MAILVIEWER_CACHE', 'default')
MAILVIEWER_DATABASE_BACKEND_MODEL = getattr(settings, 'MAILVIEWER_DATABASE_BACKEND_MODEL', 'mail_viewer_database_backend.EmailMessage')
