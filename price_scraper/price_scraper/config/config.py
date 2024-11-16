from kombu import Queue
from celery.schedules import crontab
from price_scraper.settings import REDIS_URL

# Queue Names
HIGH_PRIORITY_QUEUE = REDIS_URL
LOW_PRIORITY_QUEUE = REDIS_URL

# Celery Configuration for Queues
QUEUES = (
    Queue(HIGH_PRIORITY_QUEUE, routing_key='high_priority.#'),  # High-priority queue
    Queue(LOW_PRIORITY_QUEUE, routing_key='low_priority.#'),    # Low-priority queue
)

# Default routing settings
ROUTES = {
    'price_scraper.tasks.user_triggered_scrape': {'queue': HIGH_PRIORITY_QUEUE, 'routing_key': 'high_priority.user_triggered'},
    'price_scraper.tasks.auto_triggered_scrape': {'queue': LOW_PRIORITY_QUEUE, 'routing_key': 'low_priority.auto_triggered'},
}

# For periodic task scheduling
CELERY_BEAT_SCHEDULE = {
    'scrape-every-hour': {
        'task': 'price_scraper.tasks.auto_scrape.scrape_low_priority_jobs',
        'schedule': crontab(minute=0, hour='*'),  # every hour
    },
}
