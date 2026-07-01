from __future__ import annotations

import pandas as pd


def summarize_equity_curve(equity_curve: list[dict[str, float | str]], initial_cash: float) -> dict[str, float]:
    if not equity_curve:
        return {
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "ending_equity": initial_cash,
        }

    equity = pd.DataFrame(equity_curve)
    values = equity["equity"].astype(float)
    running_max = values.cummax()
    drawdown = (values - running_max) / running_max * 100
    ending_equity = float(values.iloc[-1])

    return {
        "total_return_pct": round(((ending_equity / initial_cash) - 1) * 100, 4),
        "max_drawdown_pct": round(float(drawdown.min()), 4),
        "ending_equity": round(ending_equity, 4),
    }
