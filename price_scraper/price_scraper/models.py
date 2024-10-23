from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    amazon_url = models.URLField(max_length=255, null=True, blank=True)
    flipkart_url = models.URLField(max_length=255, null=True, blank=True)

class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    source =  models.CharField(max_length=255)
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
