import pandas as pd
import matplotlib.pyplot as plt


def performance_auswerten(trades, startkapital=10000):
    kapital = startkapital
    entwicklung = [kapital]

    for trade in trades:
        kapital += trade
        entwicklung.append(kapital)

    equity = pd.DataFrame({
        "Trade": range(len(entwicklung)),
        "Kapital": entwicklung
    })

    max_kapital = equity["Kapital"].cummax()
    drawdown = (equity["Kapital"] - max_kapital) / max_kapital * 100

    print("\n========= PERFORMANCE =========")
    print(f"Startkapital:      {startkapital:,.2f} $")
    print(f"Endkapital:        {kapital:,.2f} $")
    print(f"Gesamtrendite:     {((kapital / startkapital) - 1) * 100:.2f}%")
    print(f"Max Drawdown:      {drawdown.min():.2f}%")
    print("===============================\n")

    plt.figure(figsize=(12, 6))
    plt.plot(equity["Kapital"])
    plt.title("TradingIA Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("Kapital ($)")
    plt.grid(True)
    plt.show()