from kombu import Queue
from celery.schedules import crontab

# Queue Names
HIGH_PRIORITY_QUEUE = "high_priority_jobs"
LOW_PRIORITY_QUEUE = "low_priority_jobs"

# Celery Configuration for Queues
CELERY_QUEUES = (
    Queue(HIGH_PRIORITY_QUEUE, routing_key='high_priority.#'),  # High-priority queue
    Queue(LOW_PRIORITY_QUEUE, routing_key='low_priority.#'),    # Low-priority queue
)

# Default routing settings
CELERY_ROUTES = {
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
