# News & Market Intelligence Engine

Die News & Market Intelligence Engine ist eine neue modulare Komponente fuer TradingIA. Sie bereitet die Architektur fuer spaetere News-Anbieter vor, ohne bereits kostenpflichtige Live-News-APIs einzubauen.

## Ziel

Fuer Daytrading koennen News, Earnings, Analystenmeldungen, Partnerships, FDA-Entscheidungen und rechtliche Risiken wichtiger sein als reine technische Indikatoren. Diese Engine bewertet solche Nachrichten zunaechst regelbasiert und testbar.

## Provider-Schnittstelle

News-Anbieter implementieren:

```python
def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
    ...
```

Aktuell gibt es weiterhin `MockNewsProvider` fuer Tests und lokale Experimente. Zusaetzlich gibt es `FinnhubNewsProvider`, der echte Unternehmensnachrichten pro Ticker laden kann, wenn ein API-Key vorhanden ist. Weitere Anbieter wie Polygon, Benzinga, Alpaca oder Broker-News koennen spaeter ueber dieselbe Schnittstelle ergaenzt werden.

## Bewertete Faktoren

- positive Begriffe
- negative Begriffe
- Earnings / Guidance
- Analyst Upgrade / Downgrade
- Partnership / Deal
- FDA / Approval
- Lawsuit / Investigation

## Ausgabe

Die Engine liefert pro Aktie:

- Aktie
- NewsScore
- Sentiment
- Anzahl News
- wichtigste Gruende

## Hinweis

Der NewsScore ist eine grobe regelbasierte Einschaetzung. Er ersetzt keine echte Nachrichtenanalyse und behauptet keine sichere Kursvorhersage. Live-News-APIs werden bewusst erst in spaeteren Schritten integriert.


## Finnhub Integration

Der `FinnhubNewsProvider` liest den API-Key aus der Umgebungsvariable `FINNHUB_API_KEY` oder aus einer lokalen `.env`-Datei im Projektverzeichnis. Es duerfen keine echten API-Keys in Git gespeichert werden.

Beispiel fuer eine lokale `.env`-Datei:

```env
FINNHUB_API_KEY=dein_lokaler_key
```

Wenn kein API-Key vorhanden ist oder Finnhub einen Fehler liefert, gibt der Provider eine leere Nachrichtenliste zurueck. Dadurch bleiben Scanner, GUI und Research-Laeufe stabil. Der bestehende `NewsIntelligenceEngine` kann die Finnhub-Nachrichten direkt bewerten und daraus den `NewsScore` berechnen. Dieser `NewsScore` kann anschliessend als Teil-Score in die Master Decision Engine eingehen.

```python
from tradingia.news import FinnhubNewsProvider, NewsIntelligenceEngine

provider = FinnhubNewsProvider()
engine = NewsIntelligenceEngine(provider)
result = engine.score_ticker("AAPL")
```
