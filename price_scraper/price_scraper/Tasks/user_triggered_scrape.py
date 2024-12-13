from price_scraper.scrapers.amazon_scraper import AmazonScraper
from price_scraper.scrapers.flipkart_scraper import FlipkartScraper
from price_scraper.services.storage_service import StorageService
from price_scraper.tasks.auto_scrape import scrape_low_priority_jobs
from price_scraper.config.config import HIGH_PRIORITY_QUEUE, LOW_PRIORITY_QUEUE
from redis import Redis
import json
import requests
from price_scraper.celery import app

redis_conn = Redis(host='redis', port=6379, db=1)

# StorageService handles cache and DB interactions
storage_service = StorageService()


@app.task(queue=HIGH_PRIORITY_QUEUE, routing_key='high_priority.user_triggered_scrape')
def user_triggered_scrape(product_data):
    """
    Synchronous Celery task for user-triggered scraping.
    """

    product_name = product_data['product_name']
    flipkart_url = product_data.get('flipkart_url')
    amazon_url = product_data.get('amazon_url')
    user_callback_url = product_data.get('callback_url')  # URL to send the result back to

    print(f"Started scraping for product: {product_name}")

    # Scrape from Amazon and Flipkart
    scraped_data = {}
    if amazon_url:
        scraped_data['amazon_price'] = scrape_and_update(AmazonScraper(), amazon_url, product_name, 'Amazon')
    if flipkart_url:
        scraped_data['flipkart_price'] = scrape_and_update(FlipkartScraper(), flipkart_url, product_name, 'Flipkart')

    # Send results back to the user
    if user_callback_url:
        send_result_to_user(user_callback_url, {
            "product_name": product_name,
            "amazon_price": scraped_data.get('amazon_price'),
            "flipkart_price": scraped_data.get('flipkart_price'),
        })

    # Transfer the job to the low-priority queue
    transfer_to_low_priority(product_data)


def scrape_and_update(scraper, url, product_name, source):
    """
    Scrapes the price and updates cache and database.
    """
    try:
        price = scraper.get_price(url)
        if price:
            # Update cache and database
            storage_service.store(product_name, source, price)
            print(f"{source}: Price updated to {price} for {product_name}")
            return price
        else:
            print(f"{source}: No price found for {product_name}")
            return None
    except Exception as e:
        print(f"Error scraping {source} for {product_name}: {e}")
        return None


def send_result_to_user(callback_url, result):
    """
    Sends the scraping result back to the user synchronously.
    """
    try:
        response = requests.post(callback_url, json=result)
        if response.status_code == 200:
            print(f"Result sent to {callback_url}")
        else:
            print(f"Failed to send result to {callback_url}, Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending result to {callback_url}: {e}")


def transfer_to_low_priority(product_data):
    """
    Transfers the job to the low-priority queue after the user-triggered scrape.
    """

    print(f"Product data after json: " , product_data)
    redis_conn.rpush(LOW_PRIORITY_QUEUE, product_data)
    print("Transferred to low-priority queue")
