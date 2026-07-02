from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tradingia.regime.models import MarketRegime, RegimeSnapshot


REQUIRED_COLUMNS = {"symbol", "timestamp", "high", "low", "close"}


@dataclass(frozen=True)
class MarketRegimeEngine:
    fast_ema_window: int = 20
    slow_ema_window: int = 50
    adx_window: int = 14
    atr_window: int = 14
    volatility_window: int = 20
    trend_adx_threshold: float = 20.0
    sideways_adx_threshold: float = 16.0
    min_ema_spread_pct: float = 0.25

    def classify(self, bars: pd.DataFrame) -> RegimeSnapshot:
        prepared = self._prepare(bars)
        indicators = self._calculate_indicators(prepared)
        if len(indicators) < 2:
            raise ValueError("Market regime detection requires enough complete indicator rows")

        latest = indicators.iloc[-1]
        ema_spread_pct = ((latest["ema_fast"] - latest["ema_slow"]) / latest["ema_slow"]) * 100
        ema_slope = latest["ema_slow"] - indicators["ema_slow"].iloc[-2]
        trend_is_strong = latest["adx"] >= self.trend_adx_threshold
        trend_is_weak = latest["adx"] <= self.sideways_adx_threshold
        spread_is_small = abs(ema_spread_pct) < self.min_ema_spread_pct

        if trend_is_strong and ema_spread_pct > self.min_ema_spread_pct and ema_slope > 0:
            regime = MarketRegime.BULL
            reason = "fast EMA above slow EMA, rising slow EMA, and ADX confirms trend strength"
        elif trend_is_strong and ema_spread_pct < -self.min_ema_spread_pct and ema_slope < 0:
            regime = MarketRegime.BEAR
            reason = "fast EMA below slow EMA, falling slow EMA, and ADX confirms trend strength"
        elif trend_is_weak or spread_is_small:
            regime = MarketRegime.SIDEWAYS
            reason = "weak trend strength or narrow EMA spread indicates range-bound conditions"
        elif ema_spread_pct > 0 and ema_slope >= 0:
            regime = MarketRegime.BULL
            reason = "EMA structure is constructive, but trend strength is moderate"
        elif ema_spread_pct < 0 and ema_slope <= 0:
            regime = MarketRegime.BEAR
            reason = "EMA structure is defensive, but trend strength is moderate"
        else:
            regime = MarketRegime.SIDEWAYS
            reason = "mixed trend signals do not confirm bull or bear conditions"

        return RegimeSnapshot(
            symbol=str(latest["symbol"]),
            timestamp=latest["timestamp"].to_pydatetime(),
            regime=regime,
            close=float(latest["close"]),
            ema_fast=float(latest["ema_fast"]),
            ema_slow=float(latest["ema_slow"]),
            adx=float(latest["adx"]),
            atr=float(latest["atr"]),
            volatility=float(latest["volatility"]),
            reason=reason,
        )

    def classify_many(self, bars: pd.DataFrame) -> dict[str, RegimeSnapshot]:
        prepared = self._prepare(bars)
        snapshots: dict[str, RegimeSnapshot] = {}
        for symbol, group in prepared.groupby("symbol", sort=True):
            snapshots[str(symbol)] = self.classify(group)
        return snapshots

    def _prepare(self, bars: pd.DataFrame) -> pd.DataFrame:
        missing = REQUIRED_COLUMNS.difference(bars.columns)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"Market regime bars are missing required columns: {names}")

        minimum_rows = max(self.slow_ema_window, self.adx_window * 2, self.atr_window, self.volatility_window) + 2
        prepared = bars.copy()
        prepared["timestamp"] = pd.to_datetime(prepared["timestamp"])
        prepared = prepared.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

        if len(prepared) < minimum_rows:
            raise ValueError(f"Market regime detection requires at least {minimum_rows} bars")

        return prepared

    def _calculate_indicators(self, bars: pd.DataFrame) -> pd.DataFrame:
        result = bars.copy()
        result["ema_fast"] = result["close"].ewm(span=self.fast_ema_window, adjust=False).mean()
        result["ema_slow"] = result["close"].ewm(span=self.slow_ema_window, adjust=False).mean()
        result["atr"] = self._average_true_range(result)
        result["adx"] = self._adx(result)
        result["volatility"] = result["close"].pct_change().rolling(self.volatility_window).std() * 100
        return result.dropna().reset_index(drop=True)

    def _average_true_range(self, bars: pd.DataFrame) -> pd.Series:
        previous_close = bars["close"].shift(1)
        true_range = pd.concat(
            [
                bars["high"] - bars["low"],
                (bars["high"] - previous_close).abs(),
                (bars["low"] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return true_range.rolling(self.atr_window).mean()

    def _adx(self, bars: pd.DataFrame) -> pd.Series:
        high = bars["high"]
        low = bars["low"]
        previous_high = high.shift(1)
        previous_low = low.shift(1)
        up_move = high - previous_high
        down_move = previous_low - low

        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        true_range = self._true_range(bars)
        atr_sum = true_range.rolling(self.adx_window).sum()

        plus_di = 100 * plus_dm.rolling(self.adx_window).sum() / atr_sum
        minus_di = 100 * minus_dm.rolling(self.adx_window).sum() / atr_sum
        denominator = (plus_di + minus_di).replace(0, pd.NA)
        dx = ((plus_di - minus_di).abs() / denominator) * 100
        return dx.rolling(self.adx_window).mean()

    def _true_range(self, bars: pd.DataFrame) -> pd.Series:
        previous_close = bars["close"].shift(1)
        return pd.concat(
            [
                bars["high"] - bars["low"],
                (bars["high"] - previous_close).abs(),
                (bars["low"] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
