from __future__ import annotations

import argparse
from pathlib import Path

from tradingia.performance_center import export_performance_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Erstellt TradingIA Performance-Center-Reports.")
    parser.add_argument("--dataset-path", default="data/prediction_dataset.csv")
    parser.add_argument("--output-dir", default="reports/performance")
    args = parser.parse_args(argv)

    dataset_path = Path(args.dataset_path)
    if not dataset_path.exists():
        print(f"Prediction-Dataset nicht gefunden: {dataset_path}")
        return 0

    try:
        analysis = export_performance_report(dataset_path, args.output_dir)
    except Exception as error:
        print(f"Performance-Report konnte nicht erstellt werden: {error}")
        return 1

    print("Performance-Report erstellt.")
    print(f"Gelabelte Zeilen: {analysis.labeled_rows}")
    print(f"Belastbare Aussage: {'Ja' if analysis.is_statistically_reliable else 'Nein'}")
    print(f"Ausgabeordner: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
