from django.test import TestCase
from api.models import StockPrice
from api.backtest import run_backtest

class BacktestTestCase(TestCase):
    def setUp(self):
        StockPrice.objects.create(
            symbol='AAPL',
            date='2023-01-01',
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            close_price=150.0,
            volume=1000000
        )
        StockPrice.objects.create(
            symbol='AAPL',
            date='2023-01-02',
            open_price=151.0,
            high_price=153.0,
            low_price=150.0,
            close_price=152.0,
            volume=1200000
        )

    def test_run_backtest(self):
        result = run_backtest('AAPL', 10000, 2, 3)
        self.assertIn('total_return', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('num_trades', result)
        self.assertIn('final_portfolio_value', result)