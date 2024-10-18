import io
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
from .services import fetch_stock_data
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


class PredictStockPriceView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        symbol = request.data.get('symbol')
        if not symbol:
            logger.error("Stock symbol is missing from the request.")
            return Response({'error': 'Stock symbol is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            api_key = ALPHA_VANTAGE_API_KEY
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            response_data = response.json()

            if "Time Series (Daily)" not in response_data:
                logger.error(f"No data found for the symbol: {symbol}")
                return Response({'error': 'No data found for the given symbol'}, status=status.HTTP_404_NOT_FOUND)

        except requests.RequestException as e:
            logger.exception(f"Error while fetching data from Alpha Vantage for symbol {symbol}: {str(e)}")
            return Response({'error': 'An error occurred while fetching stock data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            time_series = response_data["Time Series (Daily)"]
            sorted_dates = sorted(time_series.keys(), reverse=True)[:30]
            stock_prices = [
                StockPrice(
                    symbol=symbol,
                    date=date,
                    open_price=float(time_series[date]["1. open"]),
                    high_price=float(time_series[date]["2. high"]),
                    low_price=float(time_series[date]["3. low"]),
                    close_price=float(time_series[date]["4. close"]),
                    volume=int(time_series[date]["6. volume"]),
                )
                for date in sorted_dates
            ]

            StockPrice.objects.bulk_create(stock_prices, ignore_conflicts=True)

        except Exception as e:
            logger.exception(f"An error occurred while processing or saving stock data for symbol {symbol}: {str(e)}")
            return Response({'error': 'An error occurred while saving stock data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            model = joblib.load('/models/prediction-model.pkl')
        except FileNotFoundError:
            logger.critical("Model file not found.")
            return Response({'error': 'Model file not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception(f"An error occurred while loading the model: {str(e)}")
            return Response({'error': 'An error occurred while loading the model'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            last_day = (stock_prices[0].date - stock_prices[-1].date).days
            future_days = np.array(range(last_day + 1, last_day + 31)).reshape(-1, 1)
            predicted_prices = model.predict(future_days)
        except Exception as e:
            logger.exception(f"An error occurred during model prediction: {str(e)}")
            return Response({'error': 'An error occurred during model prediction'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            prediction_objects = []
            start_date = stock_prices[0].date + timedelta(days=1)
            for i in range(30):
                prediction_date = start_date + timedelta(days=i)
                prediction_objects.append(Prediction(symbol=symbol, date=prediction_date, predicted_price=predicted_prices[i]))

            Prediction.objects.bulk_create(prediction_objects)
        except Exception as e:
            logger.exception(f"An error occurred while saving predictions to the database: {str(e)}")
            return Response({'error': 'An error occurred while saving predictions'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"Successfully generated predictions for symbol: {symbol}")
        return redirect(f'/api/generate-report/?symbol={symbol}')


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