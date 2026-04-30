from __future__ import annotations

FRED_SERIES: dict[str, str] = {
    "VIX": "VIXCLS",
    "UST_3M": "DGS3MO",
    "UST_2Y": "DGS2",
    "UST_3Y": "DGS3",
    "UST_5Y": "DGS5",
    "UST_7Y": "DGS7",
    "UST_10Y": "DGS10",
    "UST_10Y_2Y": "T10Y2Y",
    "HY_OAS": "BAMLH0A0HYM2",
    "HY_YIELD": "BAMLH0A0HYM2EY",
}

CARD_BG: dict[str, str] = {
    "good": "#1a3d2a",
    "neutral": "#1a2d4d",
    "bad": "#3d1a1a",
    "info": "#1a2d4d",
    "very_risk_on": "#0f3d1f",
    "risk_on": "#1a3d4d",
    "watch": "#3d3d1a",
    "risk_off": "#3d3d1a",
    "very_risk_off": "#4d1a1a",
    "agg": "#2a2a2a",
}

CARD_BORDER: dict[str, str] = {
    "good": "#4ade80",
    "neutral": "#60a5fa",
    "bad": "#ef4444",
    "info": "#60a5fa",
    "very_risk_on": "#22c55e",
    "risk_on": "#06b6d4",
    "watch": "#eab308",
    "risk_off": "#eab308",
    "very_risk_off": "#ff6b6b",
    "agg": "#666666",
}

REGIME_LABELS: dict[int, str] = {
    1: "Regime 1: Very Risk On",
    2: "Regime 2: Risk On",
    3: "Regime 3: Risk Off",
    4: "Regime 4: Very Risk Off",
}

REGIME_COLORS: dict[int, str] = {
    1: "rgba(34,197,94,0.18)",
    2: "rgba(6,182,212,0.15)",
    3: "rgba(234,179,8,0.15)",
    4: "rgba(239,68,68,0.18)",
}

DEFAULT_THRESHOLDS: dict[str, float] = {
    "vix": 30.0,
    "oas_z": 0.0,
    "ppr_low": 0.2,
    "ppr_high": 0.8,
}

CARD_BG_LIGHT: dict[str, str] = {
    "good": "#dcfce7",
    "neutral": "#dbeafe",
    "bad": "#fee2e2",
    "info": "#dbeafe",
    "very_risk_on": "#bbf7d0",
    "risk_on": "#cffafe",
    "watch": "#fef9c3",
    "risk_off": "#fef9c3",
    "very_risk_off": "#fecaca",
    "agg": "#f1f5f9",
}

CARD_BORDER_LIGHT: dict[str, str] = {
    "good": "#16a34a",
    "neutral": "#2563eb",
    "bad": "#dc2626",
    "info": "#2563eb",
    "very_risk_on": "#15803d",
    "risk_on": "#0891b2",
    "watch": "#ca8a04",
    "risk_off": "#ca8a04",
    "very_risk_off": "#b91c1c",
    "agg": "#94a3b8",
}
