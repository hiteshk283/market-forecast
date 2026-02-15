import yfinance as yf
import pandas as pd
import sqlite3
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

DB_PATH = "data/market_data.db"
TICKER = "^NSEI"   # NIFTY 50
INTERVAL = "15m"
PERIOD = "30d"


def fetch_intraday_data():
    print("Fetching 15-min intraday data...")

    df = yf.download(
        TICKER,
        interval=INTERVAL,
        period=PERIOD,
        progress=False
    )

    # Flatten columns if multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    # Convert to IST
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


def save_to_sqlite(df):

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("intraday_data", conn, if_exists="replace", index=False)
    conn.close()

    print("Data saved to SQLite.")


def main():

    df = fetch_intraday_data()
    df = add_indicators(df)

    df = df.dropna()

    save_to_sqlite(df)

    print("Data pipeline completed successfully.")


if __name__ == "__main__":
    main()
