from django.contrib import admin
from .models import StockPrice

@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'date', 'open_price', 'close_price', 'volume')
    search_fields = ('symbol', 'date')