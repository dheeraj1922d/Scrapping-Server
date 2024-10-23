import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from celery import Celery
import concurrent
from price_scraper.scrapers.amazon_scraper import AmazonScraper
from price_scraper.scrapers.flipkart_scraper import FlipkartScraper
from price_scraper.services.storage_service import StorageService
from  price_scraper.config.config import HIGH_PRIORITY_QUEUE, LOW_PRIORITY_QUEUE

# Celery setup for the high-priority job
app = Celery('user_triggered_scrape', broker=HIGH_PRIORITY_QUEUE)

# Thread pool for running blocking scraping tasks
executor = ThreadPoolExecutor(max_workers=5)

# StorageService handles cache and DB interactions
storage_service = StorageService()

@app.task
def user_triggered_scrape(product_data):
    """
    This function handles user-triggered scraping when the user requests product data.
    It scrapes the price from multiple websites, sends it to the user via a callback,
    and then updates the cache and database before transferring the job to the low-priority queue.
    """
    product_name = product_data['product_name']
    flipkart_url = product_data.get('flipkart_url')
    amazon_url = product_data.get('amazon_url')
    user_callback_url = product_data.get('callback_url')  # URL to send the result back to

    # Scraping data from different sources concurrently
    amazon_scraper = AmazonScraper()
    flipkart_scraper = FlipkartScraper()

    # Scrape data using a thread pool
    with ThreadPoolExecutor() as executor:
        futures = []
        if flipkart_url:
            futures.append(executor.submit(scrape_and_update, flipkart_scraper, flipkart_url, product_name, 'Flipkart'))
        if amazon_url:
            futures.append(executor.submit(scrape_and_update, amazon_scraper, amazon_url, product_name, 'Amazon'))

        # Wait for scraping tasks to finish
        concurrent.futures.wait(futures)

    # Once scraping is done, send the scraped data back to the user immediately
    if user_callback_url:
        result = {
            "product_name": product_name,
            "flipkart_price": storage_service.get_from_cache(product_name, 'Flipkart'),
            "amazon_price": storage_service.get_from_cache(product_name, 'Amazon')
        }
        asyncio.run(send_result_to_user(user_callback_url, result))

    # Transfer the job to the low-priority queue after sending the data
    transfer_to_low_priority(product_data)

def scrape_and_update(scraper, url, product_name, source):
    """
    Scrapes the price and updates cache and database.
    """
    price = scraper.get_price(url)
    if price:
        # Update cache and DB asynchronously
        storage_service.store_sync(product_name, source, price)

def transfer_to_low_priority(product_data):
    """
    Transfers the job to the low-priority queue after the user-triggered scrape.
    """
    low_priority_app = Celery('low_priority_queue', broker=LOW_PRIORITY_QUEUE)
    low_priority_app.send_task('auto_triggered_scrape', args=[product_data])

async def send_result_to_user(callback_url, result):
    """
    Asynchronously sends the scraping result back to the user.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(callback_url, json=result) as response:
                if response.status == 200:
                    print(f"Result sent to {callback_url} successfully.")
                else:
                    print(f"Failed to send result to {callback_url}. Status code: {response.status}")
        except Exception as e:
            print(f"Error sending result to the user: {e}")
   