import asyncio
import json
from redis import Redis
from price_scraper.scrapers.amazon_scraper import AmazonScraper  # Assume this is now async
from price_scraper.scrapers.flipkart_scraper import FlipkartScraper  # Assume this is now async
from price_scraper.services.storage_service import StorageService
from price_scraper.config.config import LOW_PRIORITY_QUEUE
from price_scraper.celery import app

# Setup Redis connection
redis_conn = Redis(host='redis', port=6379, db=1)


@app.task
async def scrape_low_priority_jobs():
    """
    Celery task that is triggered every hour to scrape products from the low-priority queue.
    """
    jobs_data_list = await get_low_priority_jobs_from_redis()
    if jobs_data_list:
        await scrape_multiple_jobs(jobs_data_list)

async def get_low_priority_jobs_from_redis():
    """
    Fetches jobs from the low-priority Redis queue.
    Returns a list of jobs (product data) to be processed.
    """
    jobs_data_list = []
    
    while True:
        job_data = redis_conn.lpop(LOW_PRIORITY_QUEUE)
        if not job_data:
            break
        # Deserialize the job data from bytes to dict (assuming JSON format)
        job_data = json.loads(job_data.decode('utf-8'))
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
    try:
        price = scraper.get_price(url)  # Assuming get_price is now async
        
        if price:
            # If price is valid, update cache and database
            storage_service.store(product_name, source, price)
        else:
            print(f"Failed to scrape price for {product_name} from {source}")
    except Exception as e:
        print(f"Error scraping {product_name} from {source}: {str(e)}")
