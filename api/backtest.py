from .models import StockPrice
import pandas as pd

def run_backtest(symbol, initial_investment, short_ma, long_ma):
    queryset = StockPrice.objects.filter(symbol=symbol).order_by('date')
    if not queryset.exists():
        raise ValueError(f"No data found for symbol {symbol}")

    data = pd.DataFrame.from_records(queryset.values())
    data.set_index('date', inplace=True)
    data.sort_index(inplace=True)

    data['short_ma'] = data['close_price'].rolling(window=short_ma).mean()
    data['long_ma'] = data['close_price'].rolling(window=long_ma).mean()

    position = 0
    cash = initial_investment
    investment_value = 0
    trades = 0
    max_drawdown = 0
    peak = 0

    for i in range(len(data)):
        if pd.isna(data['short_ma'].iloc[i]) or pd.isna(data['long_ma'].iloc[i]):
            continue

        if position == 0 and data['short_ma'].iloc[i] > data['long_ma'].iloc[i]:
            position = cash / data['close_price'].iloc[i]
            cash = 0
            trades += 1

        elif position > 0 and data['short_ma'].iloc[i] < data['long_ma'].iloc[i]:
            cash = position * data['close_price'].iloc[i]
            position = 0
            trades += 1

        investment_value = position * data['close_price'].iloc[i] if position > 0 else cash
        peak = max(peak, investment_value)
        max_drawdown = max(max_drawdown, (peak - investment_value) / peak if peak > 0 else 0)

    if position > 0:
        cash = position * data['close_price'].iloc[-1]
    total_return = (cash - initial_investment) / initial_investment * 100

    performance_summary = {
        "total_return": total_return,
        "max_drawdown": max_drawdown * 100,
        "trades_executed": trades
    }
    return performance_summary