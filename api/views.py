import io
from django.http import JsonResponse
import joblib
import requests
import numpy as np
from api.backtest import run_backtest
from api.serializers import BacktestSerializer, ItemSerializer
from .models import Item, Prediction, StockPrice
from datetime import timedelta
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
import matplotlib.pyplot as plot
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .services import fetch_stock_data, predict_stock
import os
from django.conf import settings
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

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

class AvailableSymbolsView(APIView):
    def get(self, request, *args, **kwargs):
        url = f"https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={ALPHA_VANTAGE_API_KEY}"

        try:
            response = requests.get(url)
            response.raise_for_status()

            symbols_data = response.text.splitlines()
            symbols = [line.split(',')[0] for line in symbols_data[1:]]

            if not symbols:
                return Response({'error': 'No symbols found from Alpha Vantage'}, status=status.HTTP_404_NOT_FOUND)

        except requests.RequestException as e:
            return Response({'error': 'An error occurred while fetching symbols from Alpha Vantage'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return render(request, 'stock_picker.html', {'symbols': symbols})


class PredictStockView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        symbol = request.data.get('symbol', None)
        logger.info(f"Received symbol: {symbol}")

        if not symbol:
            return JsonResponse({'error': 'No symbol provided'}, status=400)

        try:
            prediction = predict_stock(symbol)
            prediction_value = float(prediction) if isinstance(prediction, np.ndarray) else prediction
            return JsonResponse({'symbol': symbol, 'prediction': prediction_value}, status=200)

        except ValueError as ve:
            logger.error(f"ValueError: {ve}")
            return JsonResponse({'error': str(ve)}, status=400)

        except FileNotFoundError as fe:
            logger.error(f"FileNotFoundError: {fe}")
            return JsonResponse({'error': str(fe)}, status=404)

        except Exception as e:
            logger.exception(f"Unexpected error occurred: {e}")
            return JsonResponse({'error': f"Unexpected error: {str(e)}"}, status=500)


class GenerateReportView(APIView):
    def get(self, request, *args, **kwargs):
        symbol = request.query_params.get('symbol')
        if not symbol:
            return Response({'error': 'Stock symbol is required'}, status=status.HTTP_400_BAD_REQUEST)

        historical_data = StockPrice.objects.filter(symbol=symbol).order_by('date')
        predicted_data = Prediction.objects.filter(symbol=symbol).order_by('date')

        if not historical_data.exists():
            logger.warning(f"No historical data found for {symbol}. Generating partial report with predictions only.")
            historical_dates, historical_prices = [], []
        else:
            historical_dates = [record.date for record in historical_data]
            historical_prices = [record.close_price for record in historical_data]

        if not predicted_data.exists():
            return Response({'error': f'No prediction data available for {symbol}'}, status=status.HTTP_404_NOT_FOUND)

        predicted_dates = [record.date for record in predicted_data]
        predicted_prices = [record.predicted_price for record in predicted_data]

        plot.figure(figsize=(10, 5))
        if historical_dates:
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
        pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
        pdf.setTitle(f'Performance Report for {symbol}')
        pdf.drawString(100, 750, f'Performance Report for {symbol}')
        pdf.drawString(100, 730, 'Key Metrics:')
        pdf.drawString(120, 710, f'Total Days Analyzed: {len(historical_dates)}')
        pdf.drawString(120, 690, f'Number of Predictions: {len(predicted_dates)}')
        pdf.drawImage(img_buffer, 100, 400, width=400, height=200)
        pdf.save()
        pdf_buffer.seek(0)

        return render(request, 'generated_report.html', {'symbol': symbol, 'pdf_url': f'/api/generate-report/?symbol={symbol}'})

    class GeneratePredictionView(APIView):
        def get(self, request, *args, **kwargs):
            return render(request, 'generate_prediction.html')