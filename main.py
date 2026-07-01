from scanner import scan_market


def main():
    print("=" * 80)
    print("TradingIA Scanner startet...")
    print("=" * 80)

    df = scan_market()

    if df.empty:
        print("Keine Kandidaten gefunden.")
        return

    print("\nTop Trading-Kandidaten:\n")

    spalten = [
        "Aktie",
        "TradeScore",
        "KI %",
        "Empfehlung",
        "Muster",
        "Gründe",
        "Einstieg",
        "Stop-Loss",
        "Ziel",
        "Chance/Risiko",
        "Positionsgröße $",
        "Aktien",
        "Max Risiko $",
        "Heute %",
        "RSI",
        "Volumen-Faktor",
        "52W Abstand %",
        "ADX",
        "MFI",
        "ROC",
    ]

    vorhandene_spalten = [spalte for spalte in spalten if spalte in df.columns]

    print(df[vorhandene_spalten].to_string(index=False))


if __name__ == "__main__":
    main()