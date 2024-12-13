from django.contrib import admin
from .models import PriceSource, Product, PriceHistory  # Import your models

admin.site.register(PriceSource)
admin.site.register(Product)
admin.site.register(PriceHistory)
