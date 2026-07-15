from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from tradingia.ml_dataset import DEFAULT_DATASET_PATH, label_prediction_dataset
from tradingia.ml_dataset.labeler import LABEL_COLUMNS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Label offene TradingIA Prediction-Datensaetze.")
    parser.add_argument(
        "--dataset-path",
        default=str(DEFAULT_DATASET_PATH),
        help="Pfad zur prediction_dataset.csv (Standard: data/prediction_dataset.csv)",
    )
    args = parser.parse_args(argv)
    dataset_path = Path(args.dataset_path)

    if not dataset_path.exists():
        print(f"Prediction-Dataset nicht gefunden: {dataset_path}")
        print("Fuehre zuerst einen Intelligence-Scan im Modus 'Top Chancen heute' aus.")
        return 0

    try:
        labeled_dataset, summary = label_prediction_dataset(dataset_path)
    except Exception as error:
        print(f"Prediction-Dataset konnte nicht gelabelt werden: {error}")
        return 1

    open_rows = count_open_label_rows(labeled_dataset)
    print("Prediction-Dataset Labeling abgeschlossen.")
    print(f"Geladene Zeilen: {summary.rows_total}")
    print(f"Neu gelabelte Zeilen: {summary.rows_updated}")
    print(f"Weiterhin offene Zeilen: {open_rows}")
    print(f"Speicherpfad: {dataset_path}")
    return 0


def count_open_label_rows(frame: pd.DataFrame) -> int:
    if frame is None or frame.empty:
        return 0
    existing_label_columns = [column for column in LABEL_COLUMNS if column in frame.columns]
    if not existing_label_columns:
        return len(frame)
    open_mask = frame[existing_label_columns].isna() | frame[existing_label_columns].eq("")
    return int(open_mask.any(axis=1).sum())


if __name__ == "__main__":
    raise SystemExit(main())
