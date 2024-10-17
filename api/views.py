import serializers
from .models import Item
from .models import StockPrice
from .backtest import run_backtest
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        
class BacktestView(APIView):
    def post(self, request):
        symbol = request.data.get('symbol', 'AAPL')
        initial_investment = float(request.data.get('initial_investment', 10000))
        short_ma = int(request.data.get('short_ma', 50))
        long_ma = int(request.data.get('long_ma', 200))

        try:
            result = run_backtest(symbol, initial_investment, short_ma, long_ma)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)