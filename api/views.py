from .models import Prediction, StockPrice
from .backtest import run_backtest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ItemSerializer, BacktestSerializer
from .models import Item, StockPrice
from django.http import JsonResponse
from django.conf import settings
import joblib
from datetime import timedelta


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
class PredictStockPriceView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            model = joblib.load('linear_regression_model.pkl')
        except FileNotFoundError:
            return Response({'error': 'Model file not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        symbol = request.data.get('symbol')
        if not symbol:
            return Response({'error': 'Stock symbol is required'}, status=status.HTTP_400_BAD_REQUEST)

        historical_data = StockPrice.objects.filter(symbol=symbol).order_by('date')
        if not historical_data.exists():
            return Response({'error': 'No historical data found for the given symbol'}, status=status.HTTP_404_NOT_FOUND)

        try:
            model = joblib.load('linear_regression_model.pkl')
        except FileNotFoundError:
            return Response({'error': 'Model file not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except AttributeError as e:
            return Response({'error': f'Model loading error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        last_day = (historical_data.last().date - historical_data.first().date).days
        future_days = np.array(range(last_day + 1, last_day + 31)).reshape(-1, 1)

        try:
            predicted_prices = model.predict(future_days)
        except Exception as e:
            return Response({'error': f'Model prediction error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        prediction_objects = []
        start_date = historical_data.last().date + timedelta(days=1)
        for i in range(30):
            prediction_date = start_date + timedelta(days=i)
            prediction_objects.append(Prediction(symbol=symbol, date=prediction_date, predicted_price=predicted_prices[i]))

        Prediction.objects.bulk_create(prediction_objects)

        return Response({
            'symbol': symbol,
            'predictions': [
                {
                    'date': (start_date + timedelta(days=i)).isoformat(),
                    'predicted_price': predicted_prices[i]
                } for i in range(30)
            ]
        }, status=status.HTTP_200_OK)
