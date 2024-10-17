from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api.models import StockPrice
from datetime import date


class BacktestTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 1), open_price=150, high_price=155, low_price=149, close_price=152, volume=1000000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 2), open_price=152, high_price=158, low_price=151, close_price=157, volume=1200000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 3), open_price=157, high_price=160, low_price=156, close_price=159, volume=1100000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 4), open_price=159, high_price=162, low_price=157, close_price=158, volume=900000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 5), open_price=158, high_price=161, low_price=155, close_price=156, volume=950000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 6), open_price=156, high_price=160, low_price=154, close_price=159, volume=980000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 7), open_price=159, high_price=163, low_price=158, close_price=162, volume=1020000)
        StockPrice.objects.create(symbol='AAPL', date=date(2023, 1, 8), open_price=162, high_price=165, low_price=160, close_price=164, volume=1050000)
        StockPrice.objects.create(symbol='MSFT', date=date(2023, 1, 1), open_price=200, high_price=210, low_price=195, close_price=205, volume=500000)
        StockPrice.objects.create(symbol='MSFT', date=date(2023, 1, 2), open_price=205, high_price=215, low_price=200, close_price=210, volume=550000)
        StockPrice.objects.create(symbol='MSFT', date=date(2023, 1, 3), open_price=210, high_price=220, low_price=208, close_price=215, volume=600000)
        StockPrice.objects.create(symbol='MSFT', date=date(2023, 1, 4), open_price=215, high_price=225, low_price=212, close_price=220, volume=650000)
        StockPrice.objects.create(symbol='TSLA', date=date(2023, 1, 1), open_price=300, high_price=310, low_price=290, close_price=305, volume=800000)
        StockPrice.objects.create(symbol='TSLA', date=date(2023, 1, 2), open_price=305, high_price=315, low_price=300, close_price=310, volume=850000)
        StockPrice.objects.create(symbol='TSLA', date=date(2023, 1, 3), open_price=310, high_price=320, low_price=305, close_price=315, volume=900000)
        StockPrice.objects.create(symbol='TSLA', date=date(2023, 1, 4), open_price=315, high_price=325, low_price=310, close_price=320, volume=950000)
        StockPrice.objects.create(symbol='GOOGL', date=date(2023, 1, 1), open_price=2800, high_price=2850, low_price=2750, close_price=2825, volume=400000)
        StockPrice.objects.create(symbol='GOOGL', date=date(2023, 1, 2), open_price=2825, high_price=2900, low_price=2800, close_price=2880, volume=450000)
        StockPrice.objects.create(symbol='GOOGL', date=date(2023, 1, 3), open_price=2880, high_price=2920, low_price=2850, close_price=2900, volume=470000)
        StockPrice.objects.create(symbol='GOOGL', date=date(2023, 1, 4), open_price=2900, high_price=2950, low_price=2880, close_price=2920, volume=480000)
        StockPrice.objects.create(symbol='LOWVOL', date=date(2023, 1, 1), open_price=50, high_price=55, low_price=49, close_price=52, volume=1000)
        StockPrice.objects.create(symbol='LOWVOL', date=date(2023, 1, 2), open_price=52, high_price=54, low_price=50, close_price=53, volume=1200)
        StockPrice.objects.create(symbol='LOWVOL', date=date(2023, 1, 3), open_price=53, high_price=56, low_price=51, close_price=55, volume=1500)
        StockPrice.objects.create(symbol='LOWVOL', date=date(2023, 1, 4), open_price=55, high_price=58, low_price=53, close_price=57, volume=1600)

        self.valid_payload = {
            "symbol": "AAPL",
            "initial_investment": 10000,
            "short_ma": 2,
            "long_ma": 4
        }

    def test_backtest_valid_payload(self):
        response = self.client.post(reverse('backtest'), data=self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_return', response.data)
        self.assertIn('max_drawdown', response.data)
        self.assertIn('number_of_trades', response.data)

    def test_backtest_invalid_symbol(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload['symbol'] = 'INVALID'
        response = self.client.post(reverse('backtest'), data=invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_backtest_zero_initial_investment(self):
        zero_investment_payload = self.valid_payload.copy()
        zero_investment_payload['initial_investment'] = 0
        response = self.client.post(reverse('backtest'), data=zero_investment_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_backtest_negative_initial_investment(self):
        negative_investment_payload = self.valid_payload.copy()
        negative_investment_payload['initial_investment'] = -5000
        response = self.client.post(reverse('backtest'), data=negative_investment_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_backtest_short_ma_greater_than_long_ma(self):
        invalid_ma_payload = self.valid_payload.copy()
        invalid_ma_payload['short_ma'] = 10
        invalid_ma_payload['long_ma'] = 5
        response = self.client.post(reverse('backtest'), data=invalid_ma_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_backtest_no_data_for_symbol(self):
        no_data_payload = self.valid_payload.copy()
        no_data_payload['symbol'] = 'NFLX'
        response = self.client.post(reverse('backtest'), data=no_data_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_backtest_edge_case_single_day_data(self):
        StockPrice.objects.create(symbol='AMZN', date=date(2023, 1, 1), open_price=3300, high_price=3350, low_price=3250, close_price=3325, volume=300000)
        single_day_payload = {
            "symbol": "AMZN",
            "initial_investment": 10000,
            "short_ma": 1,
            "long_ma": 1
        }
        response = self.client.post(reverse('backtest'), data=single_day_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_backtest_insufficient_data_for_ma(self):
        insufficient_data_payload = self.valid_payload.copy()
        insufficient_data_payload['short_ma'] = 10
        insufficient_data_payload['long_ma'] = 20
        response = self.client.post(reverse('backtest'), data=insufficient_data_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_backtest_successful_with_different_ma(self):
        different_ma_payload = self.valid_payload.copy()
        different_ma_payload['short_ma'] = 1
        different_ma_payload['long_ma'] = 3
        response = self.client.post(reverse('backtest'), data=different_ma_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_return', response.data)
        self.assertIn('max_drawdown', response.data)
        self.assertIn('number_of_trades', response.data)