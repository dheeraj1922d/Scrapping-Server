import redis
from django.utils import timezone
from price_scraper.models import PriceHistory

class StorageService:
    def __init__(self):
        self.redis_conn = redis.Redis(host=redis, port=6379, db=1)

    def store_async(self, product_name, source, price):
        """
        Store the product price in both Redis (cache) and the relational database (history).
        """
        self.store_in_redis(product_name, source, price)
        self.store_in_db(product_name, source, price)

    def store_in_redis(self, product_name, source, price):
        """
        Store the product price in Redis cache.
        """
        redis_key = f"{product_name}_{source}"
        self.redis_conn.set(redis_key, price)
        self.redis_conn.expire(redis_key, 3600)  # Cache for 1 hour

    def store_in_db(self, product_name, source, price):
        """
        Store the product price in the relational database (history).
        """
        PriceHistory.objects.create(
            product_name=product_name,
            price=price,
            source=source,
            timestamp=timezone.now()
        )
