import io
import joblib
from tkinter import Canvas
import numpy as np
from .models import Prediction, StockPrice
from .backtest import run_backtest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ItemSerializer, BacktestSerializer
from .models import Item, StockPrice
from django.http import FileResponse, JsonResponse
from datetime import timedelta
import matplotlib.pyplot as plot
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


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

        last_day = (historical_data.last().date - historical_data.first().date).days
        future_days = np.array(range(last_day + 1, last_day + 31)).reshape(-1, 1)  
        predicted_prices = model.predict(future_days)

        prediction_objects = []
        start_date = historical_data.last().date + timedelta(days=1)
        for i in range(30):
            prediction_date = start_date + timedelta(days=i)
            prediction_objects.append(Prediction(symbol=symbol, date=prediction_date, predicted_price=predicted_prices[i]))

        Prediction.objects.bulk_create(prediction_objects)

        historical_prices = [{'date': record.date, 'close_price': record.close_price} for record in historical_data]
        predicted_prices_response = [
            {
                'date': (start_date + timedelta(days=i)).isoformat(),
                'predicted_price': predicted_prices[i]
            } for i in range(30)
        ]

        return Response({
            'symbol': symbol,
            'historical_prices': historical_prices,
            'predictions': predicted_prices_response
        }, status=status.HTTP_200_OK)

class GenerateReportView(APIView):
    def get(self, request, *args, **kwargs):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response({'error': 'Stock symbol is required'}, status=status.HTTP_400_BAD_REQUEST)

        historical_data = StockPrice.objects.filter(symbol=symbol).order_by('date')
        predicted_data = Prediction.objects.filter(symbol=symbol).order_by('date')

        if not historical_data.exists() or not predicted_data.exists():
            return Response({'error': 'No data available for the given symbol'}, status=status.HTTP_404_NOT_FOUND)

        historical_dates = [record.date for record in historical_data]
        historical_prices = [record.close_price for record in historical_data]
        predicted_dates = [record.date for record in predicted_data]
        predicted_prices = [record.predicted_price for record in predicted_data]

        plot.figure(figsize=(10, 5))
        plot.plot(historical_dates, historical_prices, label='Historical Prices', color='blue')
        plot.plot(predicted_dates, predicted_prices, label='Predicted Prices', color='red', linestyle='--')
        plot.xlabel('Date')
        plot.ylabel('Price')
        plot.title(f'Performance Report for {symbol}')
        plot.legend()
        plot.grid()

        img_buffer = io.BytesIO()
        plot.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        pdf_buffer = io.BytesIO()
        pdf = Canvas.Canvas(pdf_buffer, pagesize=letter)
        pdf.setTitle(f'Performance Report for {symbol}')
        pdf.drawString(100, 750, f'Performance Report for {symbol}')
        pdf.drawString(100, 730, 'Key Metrics:')
        pdf.drawString(120, 710, f'Total Days Analyzed: {len(historical_dates)}')
        pdf.drawString(120, 690, f'Number of Predictions: {len(predicted_dates)}')
        pdf.drawImage(img_buffer, 100, 400, width=400, height=200)
        pdf.save()
        pdf_buffer.seek(0)

        return FileResponse(pdf_buffer, as_attachment=True, filename=f'{symbol}_performance_report.pdf')