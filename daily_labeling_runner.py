from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from label_prediction_dataset import count_open_label_rows
from tradingia.ml_dataset import label_prediction_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Labelt offene TradingIA Prediction-Datensaetze zum Tagesabschluss.")
    parser.add_argument("--dataset-path", default="data/prediction_dataset.csv")
    parser.add_argument("--output-dir", default="reports/daily")
    args = parser.parse_args(argv)

    logger = _setup_logging()
    started_at = datetime.now()
    start = time.perf_counter()
    logger.info("Daily Labeling Runner gestartet um %s", started_at.isoformat(timespec="seconds"))

    dataset_path = Path(args.dataset_path)
    if not dataset_path.exists():
        logger.warning("Dataset fehlt: %s", dataset_path)
        print(f"Prediction-Dataset nicht gefunden: {dataset_path}")
        return 0

    try:
        labeled, summary = label_prediction_dataset(dataset_path)
        open_rows = count_open_label_rows(labeled)
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        duration = time.perf_counter() - start
        logger.info("Daily Labeling Runner beendet. Laufzeit %.2fs, geladen %s, neu gelabelt %s, offen %s", duration, summary.rows_total, summary.rows_updated, open_rows)
        print("Daily Labeling Runner abgeschlossen.")
        print(f"Geladene Zeilen: {summary.rows_total}")
        print(f"Neu gelabelte Zeilen: {summary.rows_updated}")
        print(f"Weiterhin offene Zeilen: {open_rows}")
        print(f"Dataset-Pfad: {dataset_path}")
        return 0
    except Exception as error:
        duration = time.perf_counter() - start
        logger.exception("Daily Labeling Runner fehlgeschlagen nach %.2fs: %s", duration, error)
        print(f"Daily Labeling Runner fehlgeschlagen: {error}")
        return 1


def _setup_logging() -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "daily_pipeline.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("tradingia.daily_labeling")


if __name__ == "__main__":
    raise SystemExit(main())
