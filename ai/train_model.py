import os
import sys
import yfinance as yf
import pandas as pd
import joblib

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feature_builder import baue_features, FEATURES


AKTIEN = [
    "AAPL", "MSFT", "NVDA", "AMD", "AMZN", "GOOGL", "META", "TSLA",
    "NFLX", "AVGO", "ORCL", "CRM", "ADBE", "INTC", "QCOM",
    "MU", "SMCI", "PLTR", "COIN", "MSTR", "HOOD", "SOFI", "RIVN",
    "UBER", "SHOP", "PYPL", "SQ", "SNOW", "NET", "DDOG",
    "JPM", "BAC", "GS", "MS", "V", "MA",
    "LLY", "UNH", "PFE", "MRNA",
    "XOM", "CVX", "OXY",
    "BA", "CAT", "GE",
    "WMT", "COST", "HD", "NKE"
]

ZEITRAUM = "10y"
INTERVAL = "1d"
ZIEL_TAGE = 5
MIN_DATENPUNKTE = 260


def baue_dataset():
    zeilen = []

    for ticker in AKTIEN:
        print(f"Lade Daten für {ticker}...")

        data = yf.download(
            ticker,
            period=ZEITRAUM,
            interval=INTERVAL,
            progress=False,
            auto_adjust=True
        )

        if len(data) < MIN_DATENPUNKTE:
            continue

        close_all = data["Close"].squeeze()

        for i in range(220, len(data) - ZIEL_TAGE):
            try:
                feature_dict = baue_features(data, index=i)

                if feature_dict is None:
                    continue

                preis = float(close_all.iloc[i])
                zukunft_preis = float(close_all.iloc[i + ZIEL_TAGE])
                zukunft_rendite = ((zukunft_preis - preis) / preis) * 100

                ziel = 1 if zukunft_rendite > 2 else 0

                zeile = {
                    "ticker": ticker,
                    **feature_dict,
                    "ziel": ziel
                }

                zeilen.append(zeile)

            except Exception:
                continue

    return pd.DataFrame(zeilen)


def main():
    print("Baue KI-Dataset mit erweitertem Feature Builder...")
    df = baue_dataset()

    if df.empty:
        print("Kein Dataset erzeugt.")
        return

    os.makedirs("ai", exist_ok=True)
    df.to_csv("ai/dataset.csv", index=False)

    X = df[FEATURES]
    y = df["ziel"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    model = XGBClassifier(
        n_estimators=700,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )

    print("Trainiere XGBoost-Modell mit neuen Features...")
    model.fit(X_train, y_train)

    prediction = model.predict(X_test)
    probability = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, prediction)
    auc = roc_auc_score(y_test, probability)

    joblib.dump(model, "ai/model.pkl")

    importances = pd.DataFrame({
        "Feature": FEATURES,
        "Wichtigkeit": model.feature_importances_
    }).sort_values(by="Wichtigkeit", ascending=False)

    importances["Wichtigkeit %"] = (importances["Wichtigkeit"] * 100).round(2)

    print("\nXGBoost KI-Training fertig.")
    print(f"Dataset-Größe: {len(df)} Beispiele")
    print(f"Genauigkeit: {round(accuracy * 100, 2)} %")
    print(f"AUC Score: {round(auc, 4)}")
    print("Modell gespeichert unter: ai/model.pkl")

    print("\nWichtigste Merkmale:")
    print(importances[["Feature", "Wichtigkeit %"]].to_string(index=False))


if __name__ == "__main__":
    main()