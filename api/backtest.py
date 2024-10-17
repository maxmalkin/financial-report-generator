import pandas as pd
from .models import StockPrice

def run_backtest(symbol, initial_investment, short_ma, long_ma):
    queryset = StockPrice.objects.filter(symbol=symbol).order_by('date')
    data = pd.DataFrame(list(queryset.values('date', 'close_price')))

    data['date'] = pd.to_datetime(data['date'])
    data.set_index('date', inplace=True)

    data['short_ma'] = data['close_price'].rolling(window=short_ma).mean()
    data['long_ma'] = data['close_price'].rolling(window=long_ma).mean()

    cash = initial_investment
    holdings = 0
    num_trades = 0
    portfolio_value = initial_investment
    max_portfolio_value = initial_investment
    max_drawdown = 0

    for i in range(len(data)):
        row = data.iloc[i]
        if pd.notna(row['short_ma']) and pd.notna(row['long_ma']):

            if row['short_ma'] < row['long_ma'] and cash > row['close_price']:
                holdings = cash / row['close_price']
                cash = 0
                num_trades += 1
            elif row['short_ma'] > row['long_ma'] and holdings > 0:
                cash = holdings * row['close_price']
                holdings = 0
                num_trades += 1

        portfolio_value = cash + holdings * row['close_price']
        max_portfolio_value = max(max_portfolio_value, portfolio_value)
        drawdown = (max_portfolio_value - portfolio_value) / max_portfolio_value
        max_drawdown = max(max_drawdown, drawdown)

    final_return = (portfolio_value - initial_investment) / initial_investment * 100

    return {
        'total_return': f'{final_return:.2f}%',
        'max_drawdown': f'{max_drawdown:.2%}',
        'num_trades': num_trades,
        'final_portfolio_value': portfolio_value
    }
