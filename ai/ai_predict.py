import joblib

from feature_builder import features_als_dataframe


model = joblib.load("ai/model.pkl")


def ki_vorhersage(feature_dict):
    daten = features_als_dataframe(feature_dict)
    wahrscheinlichkeit = model.predict_proba(daten)[0][1]
    return round(wahrscheinlichkeit * 100, 1)