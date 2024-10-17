import requests
from datetime import datetime
from .models import StockPrice
from django.conf import settings
import os

API_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

def fetch_stock_data(symbol):
    params = {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'symbol': symbol,
        'apikey': API_KEY,
        'outputsize': 'full'
    }

    response = requests.get(API_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch stock data: {response.text}")

    data = response.json().get('Time (Daily)', {})

    for date_str, daily_data in data.items():
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        StockPrice.objects.update_or_create(
            symbol=symbol,
            date=date,
            defaults={
                'open_price': daily_data['1. open'],
                'high_price': daily_data['2. high'],
                'low_price': daily_data['3. low'],
                'close_price': daily_data['4. close'],
                'volume': daily_data['6. volume']
            }
        )