from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings

DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')
if DJANGO_ENV == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'config.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'config.settings.development')
app = Celery('config')
app.conf.update(timezone='Asia/Dhaka')
app.config_from_object(settings, namespace='CELERY')

# For Autodiscover tasks
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
