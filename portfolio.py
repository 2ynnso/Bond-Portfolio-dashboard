from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:
    yf = None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_price_history(ticker: str, start: str) -> pd.Series:
    if yf is None:
        return pd.Series(dtype=float, name=ticker)
    try:
        raw = yf.download(
            ticker,
            start=start,
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=20,
        )
        if raw.empty:
            return pd.Series(dtype=float, name=ticker)

        if isinstance(raw.columns, pd.MultiIndex):
            close_cols = [c for c in raw.columns if c[0] == "Close"]
            s = raw[close_cols[0]] if close_cols else raw.iloc[:, 0]
        else:
            for col_name in ("Close", "Adj Close"):
                if col_name in raw.columns:
                    s = raw[col_name]
                    break
            else:
                s = raw.iloc[:, 0]

        if isinstance(s, pd.DataFrame):
            s = s.squeeze()

        s = pd.to_numeric(s, errors="coerce").dropna()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        s.name = ticker
        return s
    except Exception:
        return pd.Series(dtype=float, name=ticker)


def build_portfolio_nav(
    positions: list[dict],
    start_date: pd.Timestamp,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Compute portfolio NAV (base=100) and individual ticker NAVs.
    Returns (DataFrame columns=["Portfolio", ticker1, ...], warnings)
    """
    warns: list[str] = []
    price_dict: dict[str, pd.Series] = {}

    start_naive = start_date.tz_localize(None) if start_date.tzinfo else start_date

    for pos in positions:
        tkr = str(pos.get("ticker", "")).strip().upper()
        amt = float(pos.get("amount", 0.0) or 0.0)
        if not tkr or amt <= 0:
            continue
        s = fetch_price_history(tkr, start_naive.strftime("%Y-%m-%d"))
        if s.empty:
            warns.append(f"{tkr}: 가격 데이터를 가져오지 못했습니다.")
            continue
        s = s[s.index >= start_naive]
        if s.empty:
            warns.append(f"{tkr}: 선택한 기간의 데이터가 없습니다.")
            continue
        price_dict[tkr] = s

    if not price_dict:
        return pd.DataFrame(), warns

    all_dates = pd.DatetimeIndex(
        sorted(set().union(*[set(s.index.tolist()) for s in price_dict.values()]))
    )

    port_val = pd.Series(0.0, index=all_dates)
    any_added = False

    for pos in positions:
        tkr = str(pos.get("ticker", "")).strip().upper()
        amt = float(pos.get("amount", 0.0) or 0.0)
        if tkr not in price_dict or amt <= 0:
            continue
        p = price_dict[tkr].reindex(all_dates).ffill().bfill()
        init = p.iloc[0]
        if pd.isna(init) or init <= 0:
            warns.append(f"{tkr}: 시작일 가격을 확인할 수 없습니다.")
            continue
        port_val += p * (amt / init)
        any_added = True

    if not any_added or port_val.iloc[0] == 0:
        return pd.DataFrame(), warns + ["포트폴리오를 구성하지 못했습니다."]

    nav_df = pd.DataFrame(index=all_dates)
    nav_df["Portfolio"] = port_val / port_val.iloc[0] * 100

    for tkr, prices in price_dict.items():
        p = prices.reindex(all_dates).ffill().bfill()
        nav_df[tkr] = p / p.iloc[0] * 100

    return nav_df, warns


def add_benchmark_nav(nav_df: pd.DataFrame, start_date: pd.Timestamp) -> pd.DataFrame:
    """Fetch AGG and add as benchmark column if not already present."""
    if "AGG" in nav_df.columns:
        return nav_df
    start_naive = start_date.tz_localize(None) if start_date.tzinfo else start_date
    agg = fetch_price_history("AGG", start_naive.strftime("%Y-%m-%d"))
    if agg.empty:
        return nav_df
    agg = agg[agg.index >= start_naive]
    if agg.empty:
        return nav_df
    p = agg.reindex(nav_df.index).ffill().bfill()
    nav_df = nav_df.copy()
    nav_df["AGG"] = p / p.iloc[0] * 100
    return nav_df


def compute_metrics(nav: pd.Series, rf_annual: float = 0.045) -> dict[str, float]:
    nav = nav.dropna()
    if len(nav) < 5:
        return {}

    ret = nav.pct_change().dropna()
    total_ret = float(nav.iloc[-1] / nav.iloc[0] - 1)
    n_days = (nav.index[-1] - nav.index[0]).days
    years = max(n_days / 365.25, 1 / 365.25)
    ann_ret = float((1 + total_ret) ** (1 / years) - 1)
    ann_vol = float(ret.std() * np.sqrt(252))

    rf_d = rf_annual / 252
    exc = ret - rf_d
    sharpe = float(exc.mean() / exc.std() * np.sqrt(252)) if exc.std() > 0 else float("nan")

    down = exc[exc < 0]
    sortino = (
        float(exc.mean() / down.std() * np.sqrt(252))
        if len(down) > 1 and down.std() > 0
        else float("nan")
    )

    dd = (nav - nav.cummax()) / nav.cummax()
    max_dd = float(dd.min())

    return {
        "total_return": total_ret,
        "ann_return": ann_ret,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
    }
