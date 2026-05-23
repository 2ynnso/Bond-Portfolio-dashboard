from __future__ import annotations

import json
import os
from threading import Lock

import numpy as np
import pandas as pd
from cachetools import TTLCache, cached

from utils.price_fetcher import fetch_price_history as _fetch_history

try:
    import gspread
    from google.oauth2.service_account import Credentials
    _GSPREAD_AVAILABLE = True
except ImportError:
    _GSPREAD_AVAILABLE = False

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
_SHEET_COLS = ["date", "ticker", "action", "quantity", "price_usd", "fx_rate_krw"]
_NAV_BASE = 100.0
_FX_TICKER = "KRW=X"

_trades_cache = TTLCache(maxsize=4, ttl=60)
_trades_lock = Lock()


# ── Credentials helpers ───────────────────────────────────────────────────────

def _load_service_account_info() -> dict:
    """Load Google service account info from env var or st.secrets fallback."""
    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if json_str:
        return json.loads(json_str)
    try:
        import streamlit as st
        return dict(st.secrets["gcp_service_account"])
    except Exception:
        raise RuntimeError("Google service account credentials not configured. "
                           "Set GOOGLE_SERVICE_ACCOUNT_JSON env var.")


def _load_spreadsheet_id() -> str:
    """Load Google Sheets spreadsheet ID from env var or st.secrets fallback."""
    sid = os.getenv("GSHEETS_SPREADSHEET_ID", "").strip()
    if sid:
        return sid
    try:
        import streamlit as st
        return st.secrets["gsheets"]["spreadsheet_id"]
    except Exception:
        raise RuntimeError("GSHEETS_SPREADSHEET_ID not configured.")


# ── Google Sheets helpers ──────────────────────────────────────────────────────

def _get_sheets_client():
    if not _GSPREAD_AVAILABLE:
        raise RuntimeError("gspread / google-auth not installed")
    creds = Credentials.from_service_account_info(_load_service_account_info(), scopes=_SCOPES)
    return gspread.authorize(creds)


def _get_worksheet():
    client = _get_sheets_client()
    sh = client.open_by_key(_load_spreadsheet_id())
    return sh.sheet1


def is_gsheets_configured() -> bool:
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("GSHEETS_SPREADSHEET_ID"):
        return True
    try:
        import streamlit as st
        _ = st.secrets["gcp_service_account"]
        _ = st.secrets["gsheets"]["spreadsheet_id"]
        return True
    except Exception:
        return False


@cached(cache=_trades_cache, lock=_trades_lock)
def load_trades() -> pd.DataFrame:
    """Load all trade rows from Google Sheets. Raises on failure."""
    ws = _get_worksheet()
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=_SHEET_COLS)
    df = pd.DataFrame(records)
    for col in _SHEET_COLS:
        if col not in df.columns:
            df[col] = None
    df = df[_SHEET_COLS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
    df["fx_rate_krw"] = pd.to_numeric(df["fx_rate_krw"], errors="coerce")
    df["action"] = df["action"].astype(str).str.upper()
    df["ticker"] = df["ticker"].astype(str).str.upper()
    return df.dropna(subset=["date", "ticker", "quantity"]).reset_index(drop=True)


def append_trade(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price_usd: float,
    fx_rate_krw: float,
) -> bool:
    """Append one trade row to the Google Sheet. Returns True on success."""
    ws = _get_worksheet()
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(_SHEET_COLS)
    ws.append_row([date, ticker.upper(), action.upper(), quantity, price_usd, fx_rate_krw])
    _trades_cache.clear()
    return True


# ── Price helpers ──────────────────────────────────────────────────────────────

def _value_at(holdings: dict[str, float], prices: dict[str, pd.Series], fx: pd.Series, t: pd.Timestamp) -> float:
    total = 0.0
    for tkr, qty in holdings.items():
        p_series = prices.get(tkr)
        if p_series is None or p_series.empty:
            return float("nan")
        available = p_series[p_series.index <= t]
        if available.empty:
            return float("nan")
        price = float(available.iloc[-1])
        fx_available = fx[fx.index <= t]
        fx_rate = float(fx_available.iloc[-1]) if not fx_available.empty else float("nan")
        if np.isnan(fx_rate) or np.isnan(price):
            return float("nan")
        total += qty * price * fx_rate
    return total if total > 0 else float("nan")


# ── TWR NAV calculation ────────────────────────────────────────────────────────

def compute_twr_nav(trades_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Build daily TWR-based NAV series (base=100) from a trade ledger.

    TWR splits the measurement period at each trade date.  Within each
    sub-period holdings are fixed; returns from different sub-periods are
    geometrically linked so that external cash flows don't distort performance.
    """
    warns: list[str] = []

    if trades_df.empty or "date" not in trades_df.columns:
        return pd.DataFrame(), ["거래 데이터가 없습니다."]

    df = trades_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    trade_dates = sorted(df["date"].dt.normalize().unique())
    tickers = df["ticker"].unique().tolist()

    start_str = trade_dates[0].strftime("%Y-%m-%d")
    end_date = pd.Timestamp.today().normalize()

    prices: dict[str, pd.Series] = {}
    for tkr in tickers:
        s = _fetch_history(tkr, start_str)
        if s.empty:
            warns.append(f"{tkr}: 가격 데이터를 가져오지 못했습니다.")
        else:
            prices[tkr] = s

    if not prices:
        return pd.DataFrame(), warns + ["유효한 가격 데이터가 없습니다."]

    fx = _fetch_history(_FX_TICKER, start_str)
    if fx.empty:
        warns.append("KRW/USD 환율을 가져오지 못했습니다. 기본값 1350 사용.")
        date_range = pd.bdate_range(trade_dates[0], end_date)
        fx = pd.Series(1350.0, index=date_range, name=_FX_TICKER)

    all_dates = pd.bdate_range(trade_dates[0], end_date)

    nav_series: dict[pd.Timestamp, float] = {}
    value_series: dict[pd.Timestamp, float] = {}

    holdings: dict[str, float] = {}
    nav_anchor = _NAV_BASE
    base_value: float | None = None

    boundaries = list(trade_dates) + [None]

    for idx, trade_date in enumerate(boundaries):
        if base_value is not None and base_value > 0 and holdings:
            sub_start = trade_dates[idx - 1] if idx > 0 else trade_dates[0]
            sub_end_excl = trade_date

            day_filter = (all_dates >= sub_start)
            if sub_end_excl is not None:
                day_filter &= (all_dates < sub_end_excl)

            for t in all_dates[day_filter]:
                val = _value_at(holdings, prices, fx, t)
                if not np.isnan(val):
                    nav_series[t] = nav_anchor * val / base_value
                    value_series[t] = val

        if trade_date is None:
            break

        if base_value is not None and base_value > 0 and holdings:
            val_before = _value_at(holdings, prices, fx, trade_date)
            if not np.isnan(val_before):
                nav_anchor = nav_anchor * val_before / base_value

        day_trades = df[df["date"].dt.normalize() == trade_date]
        for _, row in day_trades.iterrows():
            tkr = str(row["ticker"]).strip().upper()
            qty = float(row["quantity"])
            action = str(row["action"]).upper()
            if action == "BUY":
                holdings[tkr] = holdings.get(tkr, 0.0) + qty
            elif action == "SELL":
                holdings[tkr] = holdings.get(tkr, 0.0) - qty
                if holdings.get(tkr, 0.0) <= 0:
                    holdings.pop(tkr, None)

        val_after = _value_at(holdings, prices, fx, trade_date)
        base_value = val_after if not np.isnan(val_after) else None

    if not nav_series:
        return pd.DataFrame(), warns + ["NAV를 산출하지 못했습니다."]

    nav_df = pd.DataFrame({
        "TWR_NAV": pd.Series(nav_series),
        "KRW_Value": pd.Series(value_series),
    }).sort_index()

    agg = _fetch_history("AGG", start_str)
    if not agg.empty:
        agg_aligned = agg.reindex(nav_df.index).ffill().bfill()
        nav_df["AGG"] = agg_aligned / agg_aligned.iloc[0] * _NAV_BASE
    else:
        warns.append("AGG 벤치마크 데이터를 가져오지 못했습니다.")

    return nav_df, warns


# ── Performance decomposition ──────────────────────────────────────────────────

def compute_performance_decomposition(
    trades_df: pd.DataFrame,
    nav_df: pd.DataFrame,
) -> pd.DataFrame:
    if trades_df.empty or nav_df.empty:
        return pd.DataFrame()

    df = trades_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    start_str = df["date"].min().strftime("%Y-%m-%d")
    fx = _fetch_history(_FX_TICKER, start_str)
    current_fx = float(fx.iloc[-1]) if not fx.empty else float("nan")

    rows = []
    for _, row in df[df["action"].str.upper() == "BUY"].iterrows():
        tkr = str(row["ticker"]).strip().upper()
        buy_price = float(row["price_usd"])
        buy_fx = float(row["fx_rate_krw"]) if not pd.isna(row.get("fx_rate_krw")) else float("nan")
        qty = float(row["quantity"])

        prices = _fetch_history(tkr, row["date"].strftime("%Y-%m-%d"))
        if prices.empty:
            continue
        current_price = float(prices.iloc[-1])

        if np.isnan(buy_fx) or buy_fx <= 0:
            buy_fx = float(fx[fx.index >= row["date"]].iloc[0]) if not fx.empty else float("nan")

        price_ret_usd = (current_price / buy_price - 1) if buy_price > 0 else float("nan")
        fx_ret = (current_fx / buy_fx - 1) if not np.isnan(buy_fx) and buy_fx > 0 else float("nan")
        total_ret_krw = (
            (current_price * current_fx) / (buy_price * buy_fx) - 1
            if not np.isnan(buy_fx) and buy_fx > 0 and buy_price > 0
            else float("nan")
        )

        rows.append({
            "티커": tkr,
            "매수일": row["date"].strftime("%Y-%m-%d"),
            "수량": qty,
            "가격 수익률(USD)": price_ret_usd,
            "환율 효과(KRW/USD)": fx_ret,
            "총 수익률(KRW)": total_ret_krw,
        })

    return pd.DataFrame(rows)


# ── Trade ledger → positions converter ───────────────────────────────────────

def trades_to_positions(trades_df: pd.DataFrame) -> list[dict]:
    """Convert trade ledger rows to portfolio.py-compatible positions list."""
    if trades_df.empty:
        return []
    df = trades_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    positions = []
    for ticker, group in df.groupby("ticker"):
        buys = group[group["action"].str.upper() == "BUY"]
        sells = group[group["action"].str.upper() == "SELL"]
        net_qty = float(buys["quantity"].sum()) - float(sells["quantity"].sum())
        if net_qty <= 0 or buys.empty:
            continue
        first = buys.iloc[0]
        positions.append({
            "ticker": str(ticker),
            "buy_date": first["date"].date(),
            "currency": "USD",
            "amount": float(first["quantity"]) * float(first["price_usd"]),
        })
    return positions
