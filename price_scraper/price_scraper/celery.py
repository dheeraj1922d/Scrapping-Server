
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from price_scraper.config.config   import  QUEUES, ROUTES, CELERY_BEAT_SCHEDULE
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_scraper.settings')

app = Celery('price_scraper')
app.conf.broker_connection_retry_on_startup = True

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings' , namespace='CELERY')

# # Apply additional config from config.py
app.conf.update(
    task_queues=QUEUES,
    task_routes=ROUTES,     
    beat_schedule=CELERY_BEAT_SCHEDULE,
 )

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
