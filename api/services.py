import requests
from datetime import datetime
import numpy as np
import os
from sklearn.linear_model import LinearRegression  
from sklearn import set_config
from .models import Prediction, StockPrice
import dill

API_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/linear_regression_model.pkl')

def fetch_stock_data(symbol):
    print(f"Fetching data for {symbol}...")
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': API_KEY,
        'outputsize': 'compact'
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
        raise ValueError(f"No data found for the symbol: {symbol}")

    store_stock_data(symbol)
    return data

def load_model():
    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

        with open(MODEL_PATH, 'rb') as f:
            model = dill.load(f)

        print(f"Model loaded successfully from {MODEL_PATH}")
        return model

    except ModuleNotFoundError as e:
        print(f"Compatibility issue: {str(e)}")
        print("Re-training the model with the current scikit-learn version.")
        train_model('AAPL')
        return load_model()
    
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise

def train_model(symbol):
    try:
        stock_data = fetch_stock_data(symbol)
        print(f"Training data: {stock_data}")

        X_train = np.array([stock_data[i:i + 30] for i in range(len(stock_data) - 30)])
        y_train = np.array(stock_data[30:]).reshape(-1, 1)

        model = LinearRegression()
        model.fit(X_train, y_train)
        print("Model trained successfully.")

        with open(MODEL_PATH, 'wb') as f:
            dill.dump(model, f)

        print(f"Model saved to {MODEL_PATH}")

    except Exception as e:
        print(f"Error training model: {str(e)}")
        raise
def ensure_model_exists():
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Training a new model...")
        train_model('AAPL') 

def predict_stock(symbol):
    try:
        stock_data = fetch_stock_data(symbol)
        prices = [float(data['4. close']) for date, data in sorted(stock_data.items())]
        if len(prices) < 30:
            raise ValueError("Not enough data to make a prediction.")

        input_data = np.array(prices[-30:]).reshape(1, -1)
        print(f"Input data for prediction: {input_data}")

        ensure_model_exists()
        model = load_model()

        prediction = model.predict(input_data)[0]
        print(f"Prediction: {prediction}")

        Prediction.objects.create(
            symbol=symbol,
            predicted_price=prediction,
            date=datetime.now().date()
        )

        print("Prediction saved successfully.")
        return prediction

    except ValueError as ve:
        print(f"Prediction error: {str(ve)}")
        raise ve

    except FileNotFoundError as fe:
        print(f"File not found error: {str(fe)}")
        raise fe

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise Exception(f"Error during prediction: {str(e)}")

def store_stock_data(symbol):
    print(f"Fetching and storing data for {symbol}...")

    try:
        stock_data = fetch_stock_data(symbol) 

        for date_str, daily_data in stock_data.items():
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

    except Exception as e:
        print(f"Error fetching or storing data for {symbol}: {str(e)}")
        raise