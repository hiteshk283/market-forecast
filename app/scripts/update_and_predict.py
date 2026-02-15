import os
import sqlite3
import pandas as pd
import numpy as np
import pickle
import yfinance as yf
from datetime import datetime
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# ==============================
# PATH SETUP
# ==============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "market_data.db")
PRICE_MODEL_PATH = os.path.join(MODEL_DIR, "price_model.pkl")
DIRECTION_MODEL_PATH = os.path.join(MODEL_DIR, "direction_model.pkl")

TICKER = "^NSEI"
INTERVAL = "15m"
PERIOD = "30d"


# ==============================
# FETCH + UPDATE DATA
# ==============================

def fetch_intraday_data():
    df = yf.download(TICKER, interval=INTERVAL, period=PERIOD, progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df["Datetime"] = df["Datetime"].dt.tz_convert("Asia/Kolkata")

    return df


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


def update_database(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("intraday_data", conn, if_exists="replace", index=False)
    conn.close()


# ==============================
# LOAD MODELS
# ==============================

def load_models():
    with open(PRICE_MODEL_PATH, "rb") as f:
        price_model = pickle.load(f)

    with open(DIRECTION_MODEL_PATH, "rb") as f:
        direction_model = pickle.load(f)

    return price_model, direction_model


# ==============================
# STORE PREDICTION
# ==============================

def store_prediction(result):
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            timestamp TEXT,
            current_price REAL,
            predicted_price REAL,
            expected_return REAL,
            direction TEXT,
            probability_up REAL,
            volatility TEXT,
            confidence REAL,
            trade_action TEXT
        )
    """)

    conn.execute("""
        INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["timestamp"],
        result["current_price"],
        result["predicted_price"],
        result["expected_return_percent"],
        result["direction"],
        result["probability_up"],
        result["volatility"],
        result["confidence_score"],
        result["trade_action"]
    ))

    conn.commit()
    conn.close()


# ==============================
# MAIN PROCESS
# ==============================

def main():

    print("Updating data...")
    df = fetch_intraday_data()
    df = add_indicators(df)
    df = df.dropna()

    update_database(df)

    print("Running prediction...")

    # Prepare features
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

    expected_return = float(
        ((predicted_price - current_price) / current_price) * 100
    )

    volatility = "HIGH" if latest_row["Volatility"] > 30 else \
                 "MEDIUM" if latest_row["Volatility"] > 15 else "LOW"

    trade_action = "BUY" if prob_up > 0.65 and expected_return > 0.15 else \
                   "SELL" if prob_up < 0.35 and expected_return < -0.15 else \
                   "HOLD"

    confidence = round(prob_up * 0.7 + 0.3 * 0.53, 2)

    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_price": current_price,
        "predicted_price": predicted_price,
        "expected_return_percent": expected_return,
        "direction": "UP" if prob_up > 0.5 else "DOWN",
        "probability_up": prob_up,
        "volatility": volatility,
        "confidence_score": confidence,
        "trade_action": trade_action
    }

    store_prediction(result)

    print("Prediction stored successfully.")
    print(result)


if __name__ == "__main__":
    main()
