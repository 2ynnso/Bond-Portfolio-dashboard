from __future__ import annotations

from functools import partial

import numpy as np
import pandas as pd

from config import DEFAULT_THRESHOLDS, REGIME_LABELS


def format_value(value: float, suffix: str = "", decimals: int = 2) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}{suffix}"


def format_delta(value: float, suffix: str = "", decimals: int = 2) -> str:
    if pd.isna(value):
        return "chg N/A"
    return f"chg {value:+.{decimals}f}{suffix}"


def format_signed(value: float, suffix: str = "", decimals: int = 2) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:+.{decimals}f}{suffix}"


def latest_value(frame: pd.DataFrame, column: str) -> float:
    series = frame[column].dropna() if column in frame.columns else pd.Series(dtype=float)
    return float(series.iloc[-1]) if not series.empty else np.nan


def latest_delta(frame: pd.DataFrame, column: str, periods: int = 5) -> float:
    series = frame[column].dropna() if column in frame.columns else pd.Series(dtype=float)
    if len(series) <= periods:
        return np.nan
    return float(series.iloc[-1] - series.iloc[-1 - periods])


def define_hierarchical_regime(
    row: pd.Series,
    vix_thresh: float = DEFAULT_THRESHOLDS["vix"],
    oas_z_thresh: float = DEFAULT_THRESHOLDS["oas_z"],
    ppr_low: float = DEFAULT_THRESHOLDS["ppr_low"],
    ppr_high: float = DEFAULT_THRESHOLDS["ppr_high"],
) -> int | float:
    vix = row.get("VIX", np.nan)
    if pd.notna(vix) and vix > vix_thresh:
        return 4

    oas_z = row.get("OAS_Z", np.nan)
    if pd.notna(oas_z) and oas_z >= oas_z_thresh:
        return 3

    ppr = row.get("PPR", np.nan)
    if pd.notna(ppr) and ppr < ppr_low:
        return 1
    if pd.notna(ppr) and ppr > ppr_high:
        return 4

    return 2


def compute_oas_z(macro: pd.DataFrame, window: int) -> pd.DataFrame:
    macro = macro.copy()
    min_periods = max(6, window // 4)
    macro["OAS_Z"] = macro["HY_OAS"].rolling(window, min_periods=min_periods).apply(
        lambda x: (x.iloc[-1] - x.mean()) / x.std() if len(x) > 1 and x.std() > 0 else np.nan
    )
    return macro


def compute_regimes(
    macro: pd.DataFrame,
    vix_thresh: float = DEFAULT_THRESHOLDS["vix"],
    oas_z_thresh: float = DEFAULT_THRESHOLDS["oas_z"],
    ppr_low: float = DEFAULT_THRESHOLDS["ppr_low"],
    ppr_high: float = DEFAULT_THRESHOLDS["ppr_high"],
) -> pd.DataFrame:
    macro = macro.copy()
    fn = partial(
        define_hierarchical_regime,
        vix_thresh=vix_thresh,
        oas_z_thresh=oas_z_thresh,
        ppr_low=ppr_low,
        ppr_high=ppr_high,
    )
    macro["regime_code"] = macro.apply(fn, axis=1)
    macro["regime_detailed"] = macro["regime_code"].map(REGIME_LABELS).fillna("N/A")
    macro["regime"] = macro["regime_detailed"].str.replace(r"Regime \d+: ", "", regex=True)
    return macro


def classify_regime_detailed(regime: str) -> tuple[str, str]:
    if pd.isna(regime) or regime == "N/A":
        return "info", "N/A"
    if "Very Risk On" in regime:
        return "very_risk_on", "공격적 매수 시점"
    if "Very Risk Off" in regime:
        return "very_risk_off", "현금 보유 또는 방어"
    if "Risk Off" in regime:
        return "risk_off", "방어적 포지션 전환"
    return "risk_on", "매수 포지션 강화"


def classify_vix(value: float, thresh: float = DEFAULT_THRESHOLDS["vix"]) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", f"기준 {thresh:.0f}"
    if value >= thresh:
        return "bad", "Risk Off", f"{thresh:.0f} 이상"
    if value >= 20:
        return "watch", "Watch", f"20~{thresh:.0f}"
    return "good", "Stable", "20 미만"


def classify_oas_z(value: float, thresh: float = DEFAULT_THRESHOLDS["oas_z"]) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", f"기준 {thresh:.2f}"
    if value < thresh:
        return "good", "Tight", f"{thresh:.2f} 미만"
    return "bad", "Wide", f"{thresh:.2f} 이상"


def classify_ppr(
    value: float,
    low_thresh: float = DEFAULT_THRESHOLDS["ppr_low"],
    high_thresh: float = DEFAULT_THRESHOLDS["ppr_high"],
) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", f"기준 {low_thresh} / {high_thresh}"
    if value <= low_thresh:
        return "good", "Low", f"{low_thresh} 이하"
    if value >= high_thresh:
        return "bad", "High", f"{high_thresh} 이상"
    return "neutral", "Middle", f"{low_thresh}~{high_thresh}"  # fix: was "bad"


def classify_spread(value: float) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", "10Y-2Y"
    if value < 0:
        return "bad", "Inverted", "음수"
    if value < 0.5:
        return "neutral", "Flat", "낮은 양수"
    return "good", "Positive", "정상 구간"
