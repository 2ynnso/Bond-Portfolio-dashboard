from __future__ import annotations

from threading import Lock

import pandas as pd
from cachetools import TTLCache, cached
from cachetools.keys import hashkey

try:
    import yfinance as yf
except Exception:
    yf = None

_hist_cache = TTLCache(maxsize=64, ttl=1800)
_hist_lock = Lock()

_intraday_cache = TTLCache(maxsize=32, ttl=300)
_intraday_lock = Lock()


@cached(cache=_hist_cache, lock=_hist_lock)
def fetch_price_history(ticker: str, start: str) -> pd.Series:
    """Fetch daily adjusted close prices via yfinance."""
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


@cached(cache=_intraday_cache, lock=_intraday_lock)
def fetch_intraday(ticker: str) -> pd.Series:
    """Fetch today's 5-minute close prices, converted to US/Eastern time."""
    if yf is None:
        return pd.Series(dtype=float, name=ticker)
    try:
        raw = yf.download(
            ticker,
            period="1d",
            interval="5m",
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
        if hasattr(s.index, "tz") and s.index.tz is not None:
            try:
                s.index = s.index.tz_convert("America/New_York").tz_localize(None)
            except Exception:
                s.index = s.index.tz_localize(None)
        s.name = ticker
        return s
    except Exception:
        return pd.Series(dtype=float, name=ticker)
