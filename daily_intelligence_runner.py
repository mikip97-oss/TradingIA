from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from tradingia.intelligence import IntelligencePipeline
from tradingia.ml_dataset import append_prediction_dataset
from universe import lade_standard_universum


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fuehrt den taeglichen TradingIA Intelligence-Scan aus.")
    parser.add_argument("--universe-size", type=int, default=50)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--top-candidates", type=int, default=50)
    parser.add_argument("--dataset-path", default="data/prediction_dataset.csv")
    parser.add_argument("--output-dir", default="reports/daily")
    args = parser.parse_args(argv)

    logger = _setup_logging()
    started_at = datetime.now()
    start = time.perf_counter()
    logger.info("Daily Intelligence Runner gestartet um %s", started_at.isoformat(timespec="seconds"))

    try:
        tickers = lade_standard_universum()[: max(1, args.universe_size)]
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        results = IntelligencePipeline().run(tickers, max_workers=args.max_workers)
        saved_rows = 0
        if results is not None and not results.empty:
            candidates = results.head(max(1, args.top_candidates)).copy()
            combined = append_prediction_dataset(candidates, args.dataset_path, timestamp=started_at)
            saved_rows = len(candidates)
            candidates.to_csv(Path(args.output_dir) / "daily_intelligence_results.csv", index=False, encoding="utf-8")
        duration = time.perf_counter() - start
        logger.info("Daily Intelligence Runner beendet. Laufzeit %.2fs, Aktien %s, gespeicherte Zeilen %s", duration, len(tickers), saved_rows)
        print("Daily Intelligence Runner abgeschlossen.")
        print(f"Startzeit: {started_at.isoformat(timespec='seconds')}")
        print(f"Verarbeitete Aktien: {len(tickers)}")
        print(f"Ergebniszeilen: {0 if results is None else len(results)}")
        print(f"Gespeicherte Kandidaten: {saved_rows}")
        print(f"Dataset-Pfad: {args.dataset_path}")
        print(f"Ausgabeordner: {args.output_dir}")
        return 0
    except Exception as error:
        duration = time.perf_counter() - start
        logger.exception("Daily Intelligence Runner fehlgeschlagen nach %.2fs: %s", duration, error)
        print(f"Daily Intelligence Runner fehlgeschlagen: {error}")
        return 1


def _setup_logging() -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "daily_pipeline.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("tradingia.daily_intelligence")


if __name__ == "__main__":
    raise SystemExit(main())
