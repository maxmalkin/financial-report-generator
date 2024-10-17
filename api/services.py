import requests
from datetime import datetime
from .models import StockPrice
from django.conf import settings
import os

API_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

def fetch_stock_data(symbol):
	print(f"Fetching data for {symbol}...")

	params = {
		'function': 'TIME_SERIES_DAILY',
		'symbol': symbol,
		'apikey': API_KEY,
		'outputsize': 'full'
	}

	response = requests.get(API_URL, params=params)
	print(f"Status Code: {response.status_code}")

	if response.status_code != 200:
		raise Exception(f"Failed to fetch data: {response.text}")

	response_json = response.json()
	print("API Response:", response_json)

	data = response_json.get('Time Series (Daily)', {})

	if not data:
		print(f"No data found for {symbol}")
		return

	print(f"Fetched {len(data)} entries for {symbol}")

	for date_str, daily_data in data.items():
		date = datetime.strptime(date_str, '%Y-%m-%d').date()
		print(f"Storing data for {date}...")

		StockPrice.objects.update_or_create(
			symbol=symbol,
			date=date,
			defaults={
				'open_price': float(daily_data['1. open']),
				'high_price': float(daily_data['2. high']),
				'low_price': float(daily_data['3. low']),
				'close_price': float(daily_data['4. close']),
				'volume': int(daily_data['5. volume'])
			}
		)

	print(f"Successfully fetched and stored data for {symbol}")