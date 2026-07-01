import sys
import yfinance as yf

from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from scanner import scan_market
from ai_assistant import erstelle_ki_analyse


AKTUALISIERUNG_SEKUNDEN = 60


class ScannerThread(QThread):
    fertig = Signal(object)
    fehler = Signal(str)

    def run(self):
        try:
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

        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        right_layout = QVBoxLayout()

        self.title = QLabel("TradingIA Pro Scanner")
        self.title.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.status = QLabel("Bereit.")
        self.status.setStyleSheet("font-size: 14px;")

        self.button_scan = QPushButton("Scanner einmal starten")
        self.button_scan.clicked.connect(self.scanner_starten)

        self.button_live = QPushButton("Live-Modus starten")
        self.button_live.clicked.connect(self.live_modus_umschalten)

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
        main_layout.addWidget(self.button_scan)
        main_layout.addWidget(self.button_live)
        main_layout.addLayout(content_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_tick)

    def scanner_starten(self):
        if self.thread is not None and self.thread.isRunning():
            self.status.setText("Scanner läuft bereits.")
            return

        self.button_scan.setEnabled(False)
        self.status.setText("Scanner läuft... bitte warten.")
        self.ai_text.setText("Scanner läuft...")

        self.thread = ScannerThread()
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

        self.status.setText(f"Scanner fertig. {len(df)} Kandidaten gefunden.")
        self.ai_text.setText("Klicke links auf eine Aktie für die KI-Analyse.")

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(len(df)):
            ki = float(df.iloc[row]["KI %"])
            endscore = float(df.iloc[row]["Endscore"])

            for col in range(len(df.columns)):
                value = str(df.iloc[row, col])
                item = QTableWidgetItem(value)

                # Farb-Logik nach KI und Endscore
                if ki >= 70 and endscore >= 60:
                    item.setBackground(QColor(0, 150, 70))      # stark grün
                    item.setForeground(QColor(255, 255, 255))
                elif ki >= 60:
                    item.setBackground(QColor(255, 190, 80))    # gelb/orange
                    item.setForeground(QColor(0, 0, 0))
                elif ki < 60:
                    item.setBackground(QColor(90, 90, 90))      # grau
                    item.setForeground(QColor(220, 220, 220))

                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

        if self.live_aktiv:
            self.countdown = AKTUALISIERUNG_SEKUNDEN

    def scanner_fehler(self, meldung):
        self.button_scan.setEnabled(True)
        self.status.setText("Fehler beim Scanner.")
        self.ai_text.setText(meldung)

    def aktie_ausgewaehlt(self, row, col):
        if self.df is None:
            return

        ticker = self.table.item(row, 0).text()
        self.chart_laden(ticker)

        aktie = self.df.iloc[row].to_dict()
        analyse = erstelle_ki_analyse(aktie)
        self.ai_text.setText(analyse)

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


app = QApplication(sys.argv)

window = TradingIAApp()
window.show()

sys.exit(app.exec())