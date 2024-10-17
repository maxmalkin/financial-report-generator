from django.test import TestCase
from api.models import StockPrice
from api.backtest import run_backtest

class BacktestTestCase(TestCase):
    def setUp(self):
        StockPrice.objects.create(symbol='AAPL', date='2023-01-01', open_price=145, high_price=150, low_price=143, close_price=148, volume=1000)
        StockPrice.objects.create(symbol='AAPL', date='2023-01-02', open_price=148, high_price=152, low_price=147, close_price=151, volume=1200)
        StockPrice.objects.create(symbol='AAPL', date='2023-01-03', open_price=151, high_price=155, low_price=149, close_price=154, volume=1300)
        StockPrice.objects.create(symbol='AAPL', date='2023-01-04', open_price=154, high_price=158, low_price=152, close_price=156, volume=1400)
        StockPrice.objects.create(symbol='AAPL', date='2023-01-05', open_price=156, high_price=160, low_price=155, close_price=157, volume=1500)

    def test_run_backtest(self):
        result = run_backtest('AAPL', initial_investment=10000, short_ma=2, long_ma=3)
        
        self.assertIn('total_return', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('trades_executed', result)
        self.assertGreaterEqual(result['total_return'], 0)
        self.assertGreaterEqual(result['max_drawdown'], 0)
        self.assertGreaterEqual(result['trades_executed'], 0)