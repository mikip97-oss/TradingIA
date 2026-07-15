import sys
import yfinance as yf

from datetime import datetime

from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QComboBox, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from scanner import scan_market
from daytrading_scanner import scan_daytrading_market
from ai_assistant import erstelle_ki_analyse
from tradingia.intelligence import IntelligencePipeline
from tradingia.ml_dataset import append_prediction_dataset

try:
    from config import TOP_ANZAHL
except ImportError:
    TOP_ANZAHL = 50

try:
    from universe import lade_standard_universum
except ImportError:
    lade_standard_universum = None


AKTUALISIERUNG_SEKUNDEN = 60
SWING_MODE = "swing"
DAYTRADING_MODE = "daytrading"
INTELLIGENCE_MODE = "intelligence"
INTELLIGENCE_COLUMNS = ["Rang", "Aktie", "FinalScore", "Empfehlung", "TrendScore", "Trend-Klasse"]
FALLBACK_INTELLIGENCE_TICKERS = [
    "NVDA", "TSLA", "AMD", "AAPL", "MSFT",
    "META", "AMZN", "GOOGL", "COIN", "MSTR",
    "PLTR", "HOOD", "SOFI", "SMCI", "AVGO",
]


class ScannerThread(QThread):
    fertig = Signal(object)
    fehler = Signal(str)

    def __init__(self, scanner_mode=SWING_MODE):
        super().__init__()
        self.scanner_mode = scanner_mode

    def run(self):
        try:
            if self.scanner_mode == DAYTRADING_MODE:
                df = scan_daytrading_market()
            elif self.scanner_mode == INTELLIGENCE_MODE:
                tickers = _load_intelligence_tickers()
                df = IntelligencePipeline().run(tickers)
            else:
                df = scan_market()
            self.fertig.emit(df)
        except Exception as e:
            self.fehler.emit(str(e))


class TradingIAApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TradingIA Pro")
        self.setGeometry(150, 80, 1700, 900)

        self.live_aktiv = False
        self.countdown = AKTUALISIERUNG_SEKUNDEN
        self.thread = None
        self.df = None
        self.aktiver_modus = SWING_MODE

        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        controls_layout = QHBoxLayout()
        right_layout = QVBoxLayout()

        self.title = QLabel("TradingIA Pro Scanner")
        self.title.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.status = QLabel("Bereit.")
        self.status.setStyleSheet("font-size: 14px;")

        self.scanner_mode = QComboBox()
        self.scanner_mode.addItem("Swing Scanner", SWING_MODE)
        self.scanner_mode.addItem("Daytrading Scanner", DAYTRADING_MODE)
        self.scanner_mode.addItem("Top Chancen heute", INTELLIGENCE_MODE)

        self.button_scan = QPushButton("Scanner einmal starten")
        self.button_scan.clicked.connect(self.scanner_starten)

        self.button_live = QPushButton("Live-Modus starten")
        self.button_live.clicked.connect(self.live_modus_umschalten)

        controls_layout.addWidget(QLabel("Scanner:"))
        controls_layout.addWidget(self.scanner_mode)
        controls_layout.addWidget(self.button_scan)
        controls_layout.addWidget(self.button_live)

        self.table = QTableWidget()
        self.table.cellClicked.connect(self.aktie_ausgewaehlt)

        self.figure = Figure(figsize=(7, 4))
        self.canvas = FigureCanvas(self.figure)

        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setStyleSheet("font-size: 14px;")

        right_layout.addWidget(self.canvas, 2)
        right_layout.addWidget(QLabel("KI-Analyse"), 0)
        right_layout.addWidget(self.ai_text, 1)

        content_layout.addWidget(self.table, 2)
        content_layout.addLayout(right_layout, 3)

        main_layout.addWidget(self.title)
        main_layout.addWidget(self.status)
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(content_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_tick)

    def aktueller_scanner_modus(self):
        return self.scanner_mode.currentData()

    def scanner_starten(self):
        if self.thread is not None and self.thread.isRunning():
            self.status.setText("Scanner läuft bereits.")
            return

        self.aktiver_modus = self.aktueller_scanner_modus()
        mode_label = self.scanner_mode.currentText()
        self.button_scan.setEnabled(False)
        self.status.setText(f"{mode_label} läuft... bitte warten.")
        self.ai_text.setText(f"{mode_label} läuft...")

        self.thread = ScannerThread(scanner_mode=self.aktiver_modus)
        self.thread.fertig.connect(self.scanner_fertig)
        self.thread.fehler.connect(self.scanner_fehler)
        self.thread.start()

    def scanner_fertig(self, df):
        self.df = df
        self.button_scan.setEnabled(True)

        if df is None or df.empty:
            self.status.setText("Scanner fertig, aber keine Daten gefunden.")
            self.ai_text.setText("Keine Daten gefunden.")
            return

        if self.aktiver_modus == INTELLIGENCE_MODE:
            self._intelligence_dashboard_fertig(df)
        else:
            self._scanner_tabelle_fertig(df)

        if self.live_aktiv:
            self.countdown = AKTUALISIERUNG_SEKUNDEN

    def _scanner_tabelle_fertig(self, df):
        self.status.setText(f"Scanner fertig. {len(df)} Kandidaten gefunden.")
        self.ai_text.setText("Klicke links auf eine Aktie für die Analyse.")
        self._render_table(df, list(df.columns))

    def _intelligence_dashboard_fertig(self, df):
        dataset_status = self._prediction_dataset_speichern(df)
        self.status.setText(f"Top Chancen heute fertig. {len(df)} Kandidaten bewertet. {dataset_status}")
        self.ai_text.setText("Klicke links auf eine Aktie für die Intelligence-Analyse.")
        dashboard = df.copy().reset_index(drop=True)
        dashboard.insert(0, "Rang", range(1, len(dashboard) + 1))
        self._render_table(dashboard, INTELLIGENCE_COLUMNS)

    def _prediction_dataset_speichern(self, df):
        if df is None or df.empty:
            return "Keine Datenspeicherung notwendig."
        try:
            append_prediction_dataset(df, timestamp=datetime.now())
            return "Prediction-Datensatz gespeichert."
        except Exception as error:
            return f"Prediction-Datensatz konnte nicht gespeichert werden: {error}"

    def _render_table(self, df, columns):
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        for row in range(len(df)):
            score = self._row_score(df.iloc[row])

            for col, column in enumerate(columns):
                value = str(df.iloc[row].get(column, ""))
                item = QTableWidgetItem(value)

                if score >= 80:
                    item.setBackground(QColor(0, 130, 80))
                    item.setForeground(QColor(255, 255, 255))
                elif score >= 70:
                    item.setBackground(QColor(0, 150, 70))
                    item.setForeground(QColor(255, 255, 255))
                elif score >= 60:
                    item.setBackground(QColor(255, 190, 80))
                    item.setForeground(QColor(0, 0, 0))
                else:
                    item.setBackground(QColor(90, 90, 90))
                    item.setForeground(QColor(220, 220, 220))

                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

    def scanner_fehler(self, meldung):
        self.button_scan.setEnabled(True)
        self.status.setText("Fehler beim Scanner.")
        self.ai_text.setText(meldung)

    def aktie_ausgewaehlt(self, row, col):
        if self.df is None:
            return

        aktie = self.df.iloc[row].to_dict()
        ticker = str(aktie.get("Aktie", self.table.item(row, 0).text()))
        self.chart_laden(ticker)

        if self.aktiver_modus == INTELLIGENCE_MODE:
            analyse = self._erstelle_intelligence_analyse(aktie)
        else:
            analyse = erstelle_ki_analyse(aktie)
        self.ai_text.setText(analyse)

    def _erstelle_intelligence_analyse(self, aktie):
        ticker = _value(aktie, "Aktie", "")
        lines = []
        lines.append(f"Top Chancen heute: {ticker}")
        lines.append("=" * 40)
        lines.append(f"FinalScore: {_format_value(_value(aktie, 'FinalScore', ''))}/100")
        lines.append(f"Empfehlung: {_value(aktie, 'Empfehlung', '')}")
        lines.append("")
        lines.append("Score-Details:")
        lines.append(f"TradeScore: {_format_value(_value(aktie, 'TradeScore', 'nicht verfügbar'))}")
        lines.append(f"DayTradeScore: {_format_value(_value(aktie, 'DayTradeScore', 'nicht verfügbar'))}")
        lines.append(f"CatalystScore: {_format_value(_value(aktie, 'CatalystScore', 'nicht verfügbar'))}")
        lines.append(f"NewsScore: {_format_value(_value(aktie, 'NewsScore', 'nicht verfügbar'))}")
        lines.append(f"KI %: {_format_value(_value(aktie, 'KI %', 'nicht verfügbar'))}")
        lines.append(f"Marktregime: {_value(aktie, 'Market Regime', _value(aktie, 'Regime', 'nicht verfügbar'))}")
        lines.append("")
        lines.append("Wichtigste Gründe:")
        lines.append(str(_value(aktie, "wichtigste Gründe", _value(aktie, "Gründe", "Keine Gründe vorhanden."))))

        headline = _value(aktie, "News Headline", "")
        if headline:
            lines.append("")
            lines.append("News:")
            lines.append(f"Headline: {headline}")
            lines.append(f"Quelle: {_value(aktie, 'News Quelle', '')}")
            lines.append(f"Veröffentlichungszeit: {_value(aktie, 'News Veröffentlichungszeit', '')}")

        lines.append("")
        lines.append("Hinweis: Das ist keine Anlageberatung. Das Dashboard verbindet vorhandene TradingIA-Scores zu einer priorisierten Beobachtungsliste.")
        return "\n".join(lines)

    def chart_laden(self, ticker):
        self.status.setText(f"Lade Chart für {ticker}...")

        data = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            self.status.setText(f"Keine Chartdaten für {ticker} gefunden.")
            return

        close = data["Close"].squeeze()
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ax.plot(close.index, close.values, label="Kurs")
        ax.plot(ema20.index, ema20.values, label="EMA20")
        ax.plot(ema50.index, ema50.values, label="EMA50")

        ax.set_title(f"{ticker} Kursverlauf")
        ax.set_xlabel("Datum")
        ax.set_ylabel("Preis")
        ax.legend()
        ax.grid(True)

        self.canvas.draw()
        self.status.setText(f"Chart geladen: {ticker}")

    def live_modus_umschalten(self):
        self.live_aktiv = not self.live_aktiv

        if self.live_aktiv:
            self.countdown = AKTUALISIERUNG_SEKUNDEN
            self.button_live.setText("Live-Modus stoppen")
            self.status.setText("Live-Modus aktiv.")
            self.timer.start(1000)
            self.scanner_starten()
        else:
            self.button_live.setText("Live-Modus starten")
            self.status.setText("Live-Modus gestoppt.")
            self.timer.stop()

    def timer_tick(self):
        if not self.live_aktiv:
            return

        self.countdown -= 1
        self.status.setText(f"Live-Modus aktiv. Nächster Scan in {self.countdown} Sekunden.")

        if self.countdown <= 0:
            self.scanner_starten()
            self.countdown = AKTUALISIERUNG_SEKUNDEN

    def _row_score(self, row):
        for column in ["FinalScore", "TradeScore", "DayTradeScore", "Endscore", "KI %"]:
            if column in row:
                try:
                    return float(row[column])
                except (TypeError, ValueError):
                    return 0.0
        return 0.0


def _load_intelligence_tickers():
    if lade_standard_universum is not None:
        try:
            tickers = lade_standard_universum()
            if tickers:
                return tickers[: max(1, int(TOP_ANZAHL))]
        except Exception:
            pass
    return FALLBACK_INTELLIGENCE_TICKERS[: max(1, int(TOP_ANZAHL))]


def _value(row, key, default):
    value = row.get(key, default)
    return default if value is None or value == "" else value


def _format_value(value):
    try:
        number = float(value)
        return f"{number:.1f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def main():
    app = QApplication(sys.argv)
    window = TradingIAApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
