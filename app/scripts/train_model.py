import os
import sqlite3
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
from xgboost import XGBRegressor, XGBClassifier


# ==============================
# CONFIGURATION
# ==============================

DB_PATH = "/app/data/market_data.db"
MODEL_DIR = "/app/models"

PRICE_MODEL_PATH = os.path.join(MODEL_DIR, "price_model.pkl")
DIRECTION_MODEL_PATH = os.path.join(MODEL_DIR, "direction_model.pkl")


# ==============================
# LOAD DATA
# ==============================

def load_data():

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql("SELECT * FROM intraday_data", conn)
    except Exception as e:
        conn.close()
        raise Exception("intraday_data table not found. Run data job first.") from e

    conn.close()

    return df


# ==============================
# FEATURE ENGINEERING
# ==============================

def add_extra_features(df):

    # Percentage Returns
    df["return_1"] = df["Close"].pct_change()
    df["return_3"] = df["Close"].pct_change(3)
    df["return_5"] = df["Close"].pct_change(5)

    # Momentum
    df["momentum_5"] = df["Close"] - df["Close"].shift(5)

    return df


def prepare_data(df):

    df = add_extra_features(df)

    # Target next 15-min close
    df["target_price"] = df["Close"].shift(-1)

    # Direction classification
    df["target_direction"] = np.where(
        df["target_price"] > df["Close"], 1, 0
    )

    df = df.dropna()

    print(f"Total usable rows: {len(df)}")

    if len(df) == 0:
        raise Exception("No usable data after feature engineering.")

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

    X = df[features]
    y_price = df["target_price"]
    y_direction = df["target_direction"]

    return X, y_price, y_direction


# ==============================
# TRAIN MODELS
# ==============================

def train_models(X, y_price, y_direction):

    X_train, X_test, y_price_train, y_price_test = train_test_split(
        X, y_price, test_size=0.2, shuffle=False
    )

    _, _, y_dir_train, y_dir_test = train_test_split(
        X, y_direction, test_size=0.2, shuffle=False
    )

    reg_model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8
    )

    reg_model.fit(X_train, y_price_train)

    clf_model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss"
    )

    clf_model.fit(X_train, y_dir_train)

    price_preds = reg_model.predict(X_test)
    dir_preds = clf_model.predict(X_test)

    mse = mean_squared_error(y_price_test, price_preds)
    acc = accuracy_score(y_dir_test, dir_preds)

    print(f"\nPrice Model MSE: {mse:.2f}")
    print(f"Direction Accuracy: {acc:.2f}")

    return reg_model, clf_model


# ==============================
# SAVE MODELS
# ==============================

def save_models(reg_model, clf_model):

    os.makedirs(MODEL_DIR, exist_ok=True)

    with open(PRICE_MODEL_PATH, "wb") as f:
        pickle.dump(reg_model, f)

    with open(DIRECTION_MODEL_PATH, "wb") as f:
        pickle.dump(clf_model, f)

    print("Models saved successfully.")


# ==============================
# MAIN PIPELINE
# ==============================

def main():

    print("Loading data...")
    df = load_data()

    print("Preparing data...")
    X, y_price, y_direction = prepare_data(df)

    print("Training models...")
    reg_model, clf_model = train_models(X, y_price, y_direction)

    print("Saving models...")
    save_models(reg_model, clf_model)

    print("\nTraining completed successfully.")


if __name__ == "__main__":
    main()
