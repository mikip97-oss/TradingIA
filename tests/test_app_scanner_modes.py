from pathlib import Path


def test_app_contains_scanner_mode_switch_and_daytrading_scan():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "QComboBox" in source
    assert "Swing Scanner" in source
    assert "Daytrading Scanner" in source
    assert "scan_daytrading_market" in source
    assert "scan_market" in source
    assert "ScannerThread(scanner_mode=" in source


def test_app_table_coloring_supports_daytrade_score():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "DayTradeScore" in source
    assert "_row_score" in source


def test_app_contains_intelligence_dashboard_mode():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "Top Chancen heute" in source
    assert "INTELLIGENCE_MODE" in source
    assert "IntelligencePipeline" in source
    assert "_intelligence_dashboard_fertig" in source
    assert "Rang" in source
    assert "FinalScore" in source


def test_app_intelligence_details_include_required_scores_and_news():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "TradeScore" in source
    assert "DayTradeScore" in source
    assert "CatalystScore" in source
    assert "NewsScore" in source
    assert "KI %" in source
    assert "Marktregime" in source
    assert "News Headline" in source
    assert "News Quelle" in source
    assert "News Veröffentlichungszeit" in source


def test_app_intelligence_dashboard_shows_trend_columns():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "TrendScore" in source
    assert "Trend-Klasse" in source
    assert "INTELLIGENCE_COLUMNS" in source


def test_app_intelligence_scan_persists_prediction_dataset():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "append_prediction_dataset" in source
    assert "_prediction_dataset_speichern" in source
    assert "datetime.now()" in source
    assert "Prediction-Datensatz gespeichert" in source


def test_app_prediction_dataset_save_errors_do_not_crash_gui():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "except Exception as error" in source
    assert "Prediction-Datensatz konnte nicht gespeichert werden" in source


def test_app_prediction_dataset_is_saved_only_for_intelligence_dashboard():
    source = Path("app.py").read_text(encoding="utf-8")
    intelligence_index = source.index("def _intelligence_dashboard_fertig")
    scanner_table_index = source.index("def _scanner_tabelle_fertig")
    storage_index = source.index("_prediction_dataset_speichern(df)")

    assert intelligence_index < storage_index
    assert scanner_table_index < intelligence_index
    assert "scan_market()" in source
    assert "scan_daytrading_market()" in source
