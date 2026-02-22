from fastapi import FastAPI
from fastapi import WebSocket
import asyncio
from fastapi.responses import FileResponse
import sqlite3
import pandas as pd
import numpy as np
import pickle
import os

app = FastAPI(title="Intraday Forecast Engine")

DB_PATH = "data/market_data.db"
PRICE_MODEL_PATH = "models/price_model.pkl"
DIRECTION_MODEL_PATH = "models/direction_model.pkl"

# ==============================
# LOAD MODELS ON STARTUP
# ==============================
with open(PRICE_MODEL_PATH, "rb") as f:
    price_model = pickle.load(f)

with open(DIRECTION_MODEL_PATH, "rb") as f:
    direction_model = pickle.load(f)


# ==============================
# HELPERS
# ==============================

def classify_volatility(vol):
    if vol < 15:
        return "LOW"
    elif vol < 30:
        return "MEDIUM"
    else:
        return "HIGH"


def generate_trade_action(prob_up, expected_return, volatility):

    if prob_up > 0.65 and expected_return > 0.15 and volatility != "HIGH":
        return "BUY"

    if prob_up < 0.35 and expected_return < -0.15 and volatility != "HIGH":
        return "SELL"

    return "HOLD"


def load_latest_row():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM intraday_data", conn)
    conn.close()

    # Recreate features (must match training)
    df["return_1"] = df["Close"].pct_change()
    df["return_3"] = df["Close"].pct_change(3)
    df["return_5"] = df["Close"].pct_change(5)
    df["momentum_5"] = df["Close"] - df["Close"].shift(5)

    df = df.dropna()

    latest_row = df.iloc[-1]

    features = [
        "Close",
        "EMA_9",
        "EMA_21",
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "ATR",
        "Volatility",
        "return_1",
        "return_3",
        "return_5",
        "momentum_5"
    ]

    X_latest = latest_row[features].values.reshape(1, -1)

    return latest_row, X_latest


# ==============================
# ROUTES
# ==============================

@app.get("/")
def health_check():
    return {"status": "Forecast Engine Running"}
    
@app.get("/historical")
def historical(ticker: str = "nifty"):

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM intraday_data", conn)
    conn.close()

    df = df.tail(100)

    return df.to_dict(orient="records")
    
@app.get("/signals")
def get_signals():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM predictions ORDER BY timestamp", conn)
    conn.close()
    return df.to_dict(orient="records")
    
@app.get("/performance")
def performance():

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM predictions ORDER BY timestamp", conn)
    conn.close()

    if df.empty:
        return {"error": "No signals yet"}

    df["pnl"] = df["expected_return_percent"]
    df["cumulative_pnl"] = df["pnl"].cumsum()

    sharpe = 0
    if df["pnl"].std() != 0:
        sharpe = (df["pnl"].mean() / df["pnl"].std()) * np.sqrt(252)

    return {
        "series": df[["timestamp", "cumulative_pnl"]].to_dict(orient="records"),
        "sharpe_ratio": round(sharpe, 3)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        await asyncio.sleep(30)
        await websocket.send_json({"message": "update"})


@app.get("/dashboard")
def dashboard():
    return FileResponse("app/static/dashboard.html")


@app.get("/predict")
def predict():

    latest_row, X_latest = load_latest_row()

    current_price = float(latest_row["Close"])

    predicted_price = float(price_model.predict(X_latest)[0])

    prob_up = float(direction_model.predict_proba(X_latest)[0][1])
    direction = "UP" if prob_up > 0.5 else "DOWN"

    expected_return = float(
        ((predicted_price - current_price) / current_price) * 100
    )

    volatility = classify_volatility(float(latest_row["Volatility"]))

    trade_action = generate_trade_action(prob_up, expected_return, volatility)

    confidence = float(round(prob_up * 0.7 + 0.3 * 0.53, 2))

    return {
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "expected_return_percent": round(expected_return, 3),
        "direction": direction,
        "probability_up": round(prob_up, 3),
        "volatility": volatility,
        "confidence_score": confidence,
        "trade_action": trade_action
    }

