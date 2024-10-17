from django.db import models


class Meta:
        unique_together = ('symbol', 'date')

def __str__(self):
        return f"{self.symbol} - {self.date}"
class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
class StockPrice(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
class Prediction(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    predicted_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} - {self.date}"
class PredictedStockPrice(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    predicted_price = models.FloatField()

    class Meta:
        unique_together = ('symbol', 'date')

    def __str__(self):
        return f"{self.symbol} - {self.date} - Predicted: {self.predicted_price}"
