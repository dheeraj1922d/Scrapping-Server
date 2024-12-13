import redis
from django.utils import timezone
from price_scraper.models import PriceHistory , Product , PriceSource

class StorageService:
    def __init__(self):
        try:
            self.redis_conn = redis.Redis(host='redis', port=6379, db=0)
        except redis.exceptions.ConnectionError:
            self.redis_conn = None

    def store(self, product_name, source, price):
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
        self.redis_conn.expire(redis_key, 15552000)  # Cache for 6 months (in seconds)

    def store_in_db(self, product_name, source, price):
        """
        Store the product price in the relational database (history).
        """

        # Ensure Product exists or create it
        product, creatad = Product.objects.get_or_create(name=product_name)


        # Ensure PriceSource exists or create it
        price_source, created = PriceSource.objects.get_or_create(name=source)

        # Create a new PriceHistory record
        PriceHistory.objects.create(
            product=product,
            source=price_source,
            price=price,
            timestamp=timezone.now()  # Store the current timestamp
        )
