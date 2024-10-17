from django.contrib import admin
from .models import StockPrice, Prediction
@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'date', 'open_price', 'low_price', 'close_price', 'volume')
    search_fields = ('symbol', 'date')
@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'date', 'predicted_price', 'created_at')
    search_fields = ('symbol', 'date')