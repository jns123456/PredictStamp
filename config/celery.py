import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("reputation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


def _ensure_django_ready():
    """Load Django settings (and Sentry before_send filters) on worker/beat processes.

    Celery beat can emit to Sentry via LoggingIntegration before Django's fixup
    runs; initializing here guarantees production noise filters are active.
    """
    import django

    django.setup()


_ensure_django_ready()
