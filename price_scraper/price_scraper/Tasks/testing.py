from celery import Celery
from price_scraper.config.config import HIGH_PRIORITY_QUEUE

app = Celery('testing' , broker=HIGH_PRIORITY_QUEUE)
@app.task
def testing_req():
    print("Request accepted")