from kombu import Queue
from celery.schedules import crontab

# Queue Names
HIGH_PRIORITY_QUEUE = 'high_priority'
LOW_PRIORITY_QUEUE = 'low_priority'

# Celery Configuration for Queues
QUEUES = (
    Queue(HIGH_PRIORITY_QUEUE, routing_key='high_priority.#'),  # High-priority queue
    Queue(LOW_PRIORITY_QUEUE, routing_key='low_priority.#'),    # Low-priority queue
)

# Default routing settings
ROUTES = {
    'price_scraper.tasks.user_triggered_scrape': {'queue': HIGH_PRIORITY_QUEUE, 'routing_key': 'high_priority.user_triggered_scrape'},
    'price_scraper.tasks.auto_scrape': {'queue': LOW_PRIORITY_QUEUE, 'routing_key': 'low_priority.auto_scrape'},
}

# For periodic task scheduling
CELERY_BEAT_SCHEDULE = {
    'scrape-every-hour': {
        'task': 'price_scraper.tasks.auto_scrape',
        'schedule': crontab(minute=0, hour='*'),  # every hour
    },
}
