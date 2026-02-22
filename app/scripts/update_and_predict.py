import os
import sqlite3
import pandas as pd
import numpy as np
import pickle
import yfinance as yf
from datetime import datetime, time
import pytz
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


# ==============================
# CONFIG (ABSOLUTE PATHS FOR K8s)
# ==============================

DB_PATH = "/app/data/market_data.db"
PRICE_MODEL_PATH = "/app/models/price_model.pkl"
DIRECTION_MODEL_PATH = "/app/models/direction_model.pkl"

TICKER = "^NSEI"
INTERVAL = "15m"
PERIOD = "30d"


# ==============================
# MARKET CALENDAR (INLINE)
# ==============================

def market_is_open():
    """
    Indian NSE Market hours:
    Monday–Friday
    9:15 AM to 3:30 PM IST
    """

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    # Weekend check
    if now.weekday() >= 5:
        return False

    market_open = time(9, 15)
    market_close = time(15, 30)

    return market_open <= now.time() <= market_close


# ==============================
# FETCH DATA
# ==============================

def fetch_intraday_data():
    df = yf.download(TICKER, interval=INTERVAL, period=PERIOD, progress=False)

    if df.empty:
        raise ValueError("No data fetched from Yahoo Finance.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize("UTC")

    df["Datetime"] = df["Datetime"].dt.tz_convert("Asia/Kolkata")

    return df


# ==============================
# ADD INDICATORS
# ==============================

def add_indicators(df):

    df["EMA_9"] = EMAIndicator(df["Close"], window=9).ema_indicator()
    df["EMA_21"] = EMAIndicator(df["Close"], window=21).ema_indicator()
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()

    macd = MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=14
    )
    df["ATR"] = atr.average_true_range()

    df["Volatility"] = df["Close"].rolling(window=20).std()

    return df


# ==============================
# UPDATE DATABASE
# ==============================

def update_database(df):

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("intraday_data", conn, if_exists="replace", index=False)
    conn.close()


# ==============================
# LOAD MODELS
# ==============================

def load_models():

    if not os.path.exists(PRICE_MODEL_PATH):
        raise FileNotFoundError(f"Price model not found: {PRICE_MODEL_PATH}")

    if not os.path.exists(DIRECTION_MODEL_PATH):
        raise FileNotFoundError(f"Direction model not found: {DIRECTION_MODEL_PATH}")

    with open(PRICE_MODEL_PATH, "rb") as f:
        price_model = pickle.load(f)

    with open(DIRECTION_MODEL_PATH, "rb") as f:
        direction_model = pickle.load(f)

    return price_model, direction_model


# ==============================
# STORE PREDICTION
# ==============================

def store_prediction(data):

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            current_price REAL,
            predicted_price REAL,
            expected_return REAL,
            direction TEXT,
            probability REAL,
            trade_action TEXT
        )
    """)

    conn.execute("""
        INSERT INTO predictions
        (timestamp, current_price, predicted_price, expected_return,
         direction, probability, trade_action)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["current_price"],
        data["predicted_price"],
        data["expected_return"],
        data["direction"],
        data["probability"],
        data["trade_action"]
    ))

    conn.commit()
    conn.close()
    
 def ensure_predictions_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            current_price REAL,
            predicted_price REAL,
            expected_return REAL,
            direction TEXT,
            probability REAL,
            trade_action TEXT
        )
    """)
    conn.commit()
    conn.close()



# ==============================
# MAIN PROCESS
# ==============================

def main():

    try:
        
        ensure_predictions_table()

        if not market_is_open():
            print("Market closed. Skipping execution.")
            return

        print("Fetching data...")
        df = fetch_intraday_data()

        print("Adding indicators...")
        df = add_indicators(df)
        df = df.dropna()

        update_database(df)

        print("Preparing features...")
        df["return_1"] = df["Close"].pct_change()
        df["return_3"] = df["Close"].pct_change(3)
        df["return_5"] = df["Close"].pct_change(5)
        df["momentum_5"] = df["Close"] - df["Close"].shift(5)

        df = df.dropna()
        latest_row = df.iloc[-1]

        features = [
            "Close", "EMA_9", "EMA_21", "RSI",
            "MACD", "MACD_SIGNAL", "ATR", "Volatility",
            "return_1", "return_3", "return_5", "momentum_5"
        ]

        X_latest = latest_row[features].values.reshape(1, -1)

        price_model, direction_model = load_models()

        current_price = float(latest_row["Close"])
        predicted_price = float(price_model.predict(X_latest)[0])
        prob_up = float(direction_model.predict_proba(X_latest)[0][1])

        expected_return = ((predicted_price - current_price) / current_price) * 100
        direction = "UP" if prob_up > 0.5 else "DOWN"

        trade_action = (
            "BUY" if prob_up > 0.65 else
            "SELL" if prob_up < 0.35 else
            "HOLD"
        )

        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": current_price,
            "predicted_price": predicted_price,
            "expected_return": expected_return,
            "direction": direction,
            "probability": prob_up,
            "trade_action": trade_action
        }

        store_prediction(result)

        print("Prediction stored successfully.")
        print(result)

    except Exception as e:
        print(f"Error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
