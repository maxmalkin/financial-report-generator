from django.core.management.base import BaseCommand
from api.services import fetch_stock_data

class Command(BaseCommand):
    help = 'Fetch and store stock data.'

    def add_arguments(self, parser):
        parser.add_argument('symbol', type=str, help='Stock symbol')

    def handle(self, *args, **options):
        symbol = options['symbol']
        try:
            fetch_stock_data(symbol)
            self.stdout.write(self.style.SUCCESS(f'Successful fetch for {symbol}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))
