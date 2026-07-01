import pandas as pd
import joblib

from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score

from feature_builder import FEATURES


MODEL_PATH = "ai/model.pkl"
DATASET_PATH = "ai/dataset.csv"


def auswertung_schwelle(df, schwelle):
    signale = df[df["KI %"] >= schwelle]

    if signale.empty:
        return {
            "Schwelle": schwelle,
            "Trades": 0,
            "Trefferquote": 0,
            "Ø Rendite": 0,
        }

    gewinner = signale[signale["ziel"] == 1]

    return {
        "Schwelle": schwelle,
        "Trades": len(signale),
        "Trefferquote": round(len(gewinner) / len(signale) * 100, 2),
        "Ø Rendite": round(signale["zukunft_rendite"].mean(), 2) if "zukunft_rendite" in signale.columns else 0,
    }


def main():
    print("Lade Dataset und Modell...")

    df = pd.read_csv(DATASET_PATH)
    model = joblib.load(MODEL_PATH)

    X = df[FEATURES]
    y = df["ziel"]

    wahrscheinlichkeiten = model.predict_proba(X)[:, 1]
    prediction = model.predict(X)

    df["KI %"] = wahrscheinlichkeiten * 100

    print("\nModell-Auswertung:")
    print(f"Genauigkeit: {round(accuracy_score(y, prediction) * 100, 2)} %")
    print(f"AUC: {round(roc_auc_score(y, wahrscheinlichkeiten), 4)}")
    print(f"Precision: {round(precision_score(y, prediction) * 100, 2)} %")
    print(f"Recall: {round(recall_score(y, prediction) * 100, 2)} %")

    print("\nKI-Schwellen:")
    print("=" * 50)

    ergebnisse = []

    for schwelle in [45, 50, 55, 60, 65, 70, 75, 80]:
        ergebnisse.append(auswertung_schwelle(df, schwelle))

    result = pd.DataFrame(ergebnisse)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()