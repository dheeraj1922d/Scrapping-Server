import asyncio
from concurrent.futures import ThreadPoolExecutor
from celery import Celery
from redis import Redis
from scrapers.amazon_scraper import AmazonScraper
from scrapers.flipkart_scraper import FlipkartScraper
from services.storage_service import StorageService
from price_scraper.config.config import LOW_PRIORITY_QUEUE

# Setup Redis connection
redis_conn = Redis(host='redis', port=6379, db=0)

# Celery setup for scheduling the low-priority scraping jobs
app = Celery('auto_triggered_scrap', broker=LOW_PRIORITY_QUEUE)

# Thread pool for running blocking tasks like scraping
executor = ThreadPoolExecutor(max_workers=10)

@app.task
def scrape_low_priority_jobs():
    """
    Celery task that is triggered every hour to scrape products from the low-priority queue.
    """
    jobs_data_list = get_low_priority_jobs_from_redis()
    if jobs_data_list:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(scrape_multiple_jobs(jobs_data_list))

def get_low_priority_jobs_from_redis():
    """
    Fetches jobs from the low-priority Redis queue.
    Returns a list of jobs (product data) to be processed.
    """
    jobs_data_list = []
    
    while True:
        job_data = redis_conn.lpop(LOW_PRIORITY_QUEUE)
        if not job_data:
            break
        jobs_data_list.append(job_data)

    return jobs_data_list

async def scrape_multiple_jobs(jobs_data_list):
    """
    Asynchronously scrapes prices for multiple products and updates the cache and database.
    """
    scrape_tasks = [scrape_and_update(job_data) for job_data in jobs_data_list]
    await asyncio.gather(*scrape_tasks)

async def scrape_and_update(product_data):
    """
    Scrapes the price for a given product and updates cache and database asynchronously.
    """
    product_name = product_data['product_name']
    flipkart_url = product_data.get('flipkart_url')
    amazon_url = product_data.get('amazon_url')

    # Instantiate the scrapers
    amazon_scraper = AmazonScraper()
    flipkart_scraper = FlipkartScraper()
    
    # Create a StorageService instance to handle cache and DB updates
    storage_service = StorageService()

    scrape_tasks = []
    
    # Scrape from Flipkart if URL is present
    if flipkart_url:
        scrape_tasks.append(scrape_and_store_price(flipkart_scraper, flipkart_url, product_name, 'Flipkart', storage_service))
    
    # Scrape from Amazon if URL is present
    if amazon_url:
        scrape_tasks.append(scrape_and_store_price(amazon_scraper, amazon_url, product_name, 'Amazon', storage_service))

    await asyncio.gather(*scrape_tasks)

async def scrape_and_store_price(scraper, url, product_name, source, storage_service):
    """
    Scrapes the price and stores it in cache and database.
    """
    loop = asyncio.get_event_loop()
    
    # Use thread executor to run the blocking scraping operation
    price = await loop.run_in_executor(executor, scraper.get_price, url)
    
    if price:
        # If price is valid, update cache and database
        await storage_service.store_async(product_name, source, price)

