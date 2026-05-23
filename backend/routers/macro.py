from __future__ import annotations

import math

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.schemas import MacroLatest, MacroResponse, MacroRow
from data import build_dataset, get_fred_api_key
from signals import compute_oas_z, compute_regimes

router = APIRouter()


def _safe(v) -> float | None:
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except Exception:
        return None


@router.get("/macro", response_model=MacroResponse)
def get_macro(
    years: int = Query(8, ge=1, le=15),
    oas_window: int = Query(24, ge=6, le=36),
    vix_thresh: float = Query(25.0),
    oas_z_thresh: float = Query(1.0),
    ppr_low: float = Query(0.2),
    ppr_high: float = Query(0.8),
    include_ppr: bool = Query(True),
):
    api_key = get_fred_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="FRED_API_KEY not configured")

    start_date = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)
    macro_raw, warnings, ppr_note = build_dataset(start_date, api_key, include_ppr)

    if macro_raw.empty:
        raise HTTPException(status_code=502, detail="Failed to load FRED data")

    macro_with_oas = compute_oas_z(macro_raw, oas_window)
    macro = compute_regimes(macro_with_oas, vix_thresh, oas_z_thresh, ppr_low, ppr_high)

    macro_clean = macro.dropna(how="all")

    rows: list[MacroRow] = []
    for ts, row in macro_clean.iterrows():
        rows.append(MacroRow(
            date=ts.strftime("%Y-%m-%d"),
            VIX=_safe(row.get("VIX")),
            OAS_Z=_safe(row.get("OAS_Z")),
            PPR=_safe(row.get("PPR")),
            HY_OAS=_safe(row.get("HY_OAS")),
            HY_YIELD=_safe(row.get("HY_YIELD")),
            UST_3M=_safe(row.get("UST_3M")),
            UST_2Y=_safe(row.get("UST_2Y")),
            UST_3Y=_safe(row.get("UST_3Y")),
            UST_5Y=_safe(row.get("UST_5Y")),
            UST_7Y=_safe(row.get("UST_7Y")),
            UST_10Y=_safe(row.get("UST_10Y")),
            UST_10Y_2Y=_safe(row.get("UST_10Y_2Y")),
            AGG=_safe(row.get("AGG")),
            regime=_safe(row.get("regime")),
            regime_code=_safe(row.get("regime_code")),
            regime_detailed=str(row["regime_detailed"]) if "regime_detailed" in row.index and not pd.isna(row.get("regime_detailed")) else None,
        ))

    latest_row = macro_clean.iloc[-1]
    latest_date = macro_clean.index[-1].strftime("%Y-%m-%d")
    latest_values = {
        col: _safe(latest_row[col]) if col in latest_row.index else None
        for col in macro_clean.columns
    }
    regime_code_val = _safe(latest_row.get("regime_code"))
    regime_code_int = int(regime_code_val) if regime_code_val is not None else None

    return MacroResponse(
        signals=rows,
        latest=MacroLatest(date=latest_date, values=latest_values),
        regime_code=regime_code_int,
        warnings=warnings,
        ppr_note=ppr_note,
    )
