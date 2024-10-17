from .models import StockPrice
from .backtest import run_backtest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import StockPriceSerializer, ItemSerializer, BacktestSerializer
from .models import Item
from django.shortcuts import render
from django.http import JsonResponse

def fetch_data_view(request):
    if request.method == 'GET':
        data = {"message": "Data fetched successfully."}
        return JsonResponse(data)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class BacktestView(APIView):
    def post(self, request):
        serializer = BacktestSerializer(data=request.data)
        if serializer.is_valid():
            symbol = serializer.validated_data['symbol']
            initial_investment = serializer.validated_data['initial_investment']
            short_ma = serializer.validated_data['short_ma']
            long_ma = serializer.validated_data['long_ma']

            try:
                backtest_result = run_backtest(symbol, initial_investment, short_ma, long_ma)
                return Response(backtest_result, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
