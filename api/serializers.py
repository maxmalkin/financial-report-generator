from rest_framework import serializers
from .models import StockPrice, Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        fields = '__all__'
class BacktestSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    initial_investment = serializers.FloatField(min_value=0.0)
    short_ma = serializers.IntegerField(min_value=1)
    long_ma = serializers.IntegerField(min_value=1)

    def validate(self, data):
        if data['short_ma'] >= data['long_ma']:
            raise serializers.ValidationError("Short moving average period must be less than the long moving average period.")
        return data