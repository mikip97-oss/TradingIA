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

Aktuell gibt es nur `MockNewsProvider` fuer Tests und lokale Experimente. Spaeter koennen Anbieter wie Finnhub, Polygon, Benzinga, Alpaca oder Broker-News ergaenzt werden.

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
