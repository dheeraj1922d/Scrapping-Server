import asyncio
import aiohttp
import logging
from celery import Celery
from price_scraper.scrapers.amazon_scraper import AmazonScraper
from price_scraper.scrapers.flipkart_scraper import FlipkartScraper
from price_scraper.services.storage_service import StorageService
from price_scraper.config.config import HIGH_PRIORITY_QUEUE, LOW_PRIORITY_QUEUE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Celery setup for the high-priority job
app = Celery('user_triggered_scrape' )

# StorageService handles cache and DB interactions
storage_service = StorageService()

@app.task
async def user_triggered_scrape(product_data):
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

    logger.info(f"Scraping product: {product_name}")

    # Scrape data using async functions
    tasks = []
    if flipkart_url:
        tasks.append(scrape_and_update(flipkart_scraper, flipkart_url, product_name, 'Flipkart'))
    if amazon_url:
        tasks.append(scrape_and_update(amazon_scraper, amazon_url, product_name, 'Amazon'))

    # Await for all scraping tasks to finish
    await asyncio.gather(*tasks)

    # Once scraping is done, send the scraped data back to the user immediately
    if user_callback_url:
        result = {
            "product_name": product_name,
            "flipkart_price": storage_service.get_from_cache(product_name, 'Flipkart'),
            "amazon_price": storage_service.get_from_cache(product_name, 'Amazon')
        }
        await send_result_to_user(user_callback_url, result)

    # Transfer the job to the low-priority queue after sending the data
    transfer_to_low_priority(product_data)

async def scrape_and_update(scraper, url, product_name, source):
    """
    Scrapes the price and updates cache and database asynchronously.
    """
    try:
        price = await scraper.get_price(url)
        if price:
            # Update cache and DB asynchronously
            await storage_service.store_async(product_name, source, price)
            logger.info(f"Updated price for {product_name} from {source}: {price}")
        else:
            logger.warning(f"No price found for {product_name} on {source}.")
    except Exception as e:
        logger.error(f"Error scraping {source} for {product_name}: {e}")

async def send_result_to_user(callback_url, result):
    """
    Asynchronously sends the scraping result back to the user.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(callback_url, json=result) as response:
                if response.status == 200:
                    logger.info(f"Result sent to {callback_url} successfully.")
                else:
                    logger.error(f"Failed to send result to {callback_url}. Status code: {response.status}")
        except Exception as e:
            logger.error(f"Error sending result to the user: {e}")

def transfer_to_low_priority(product_data):
    """
    Transfers the job to the low-priority queue after the user-triggered scrape.
    """
    low_priority_app = Celery('low_priority_queue', broker=LOW_PRIORITY_QUEUE)
    low_priority_app.send_task('price_scraper.tasks.auto_triggered_scrape', args=[product_data])
