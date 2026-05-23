from __future__ import annotations

import os
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd
import requests
import certifi
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from dotenv import load_dotenv

from config import FRED_SERIES

try:
    import yfinance as yf
except Exception:
    yf = None

ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(ENV_PATH)

_fred_cache = TTLCache(maxsize=8, ttl=1800)
_fred_lock = Lock()

_yf_cache = TTLCache(maxsize=16, ttl=1800)
_yf_lock = Lock()

_ppr_cache = TTLCache(maxsize=8, ttl=1800)
_ppr_lock = Lock()


def safe_zscore(series: pd.Series) -> pd.Series:
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(index=series.index, data=0.0)
    return (series - series.mean()) / std


def coerce_series(data: pd.DataFrame | pd.Series, preferred_columns: list[str] | None = None) -> pd.Series:
    if isinstance(data, pd.Series):
        series = data.copy()
    else:
        series = pd.Series(dtype=float)
        preferred_columns = preferred_columns or []
        if isinstance(data.columns, pd.MultiIndex):
            for column in data.columns:
                if column[-1] in preferred_columns or column[0] in preferred_columns:
                    series = data[column].copy()
                    break
            if series.empty and len(data.columns) > 0:
                series = data.iloc[:, 0].copy()
        else:
            for column in preferred_columns:
                if column in data.columns:
                    series = data[column].copy()
                    break
            if series.empty and len(data.columns) > 0:
                series = data.iloc[:, 0].copy()

    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]

    series = pd.to_numeric(series, errors="coerce")
    series.index = pd.to_datetime(series.index)
    return series.dropna().sort_index()


def get_fred_api_key() -> str:
    env_key = os.getenv("FRED_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        import streamlit as st
        return st.secrets.get("FRED_API_KEY", "").strip()
    except Exception:
        return ""


def _yf_cache_key(ticker, start_date, preferred_columns):
    return hashkey(ticker, start_date, tuple(preferred_columns or []))


@cached(cache=_fred_cache, lock=_fred_lock)
def fetch_fred_series(start_date: pd.Timestamp, api_key: str) -> tuple[pd.DataFrame, list[str]]:
    frames: list[pd.Series] = []
    warnings: list[str] = []

    for name, series_id in FRED_SERIES.items():
        try:
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": start_date.strftime("%Y-%m-%d"),
                },
                timeout=20,
                verify=certifi.where(),
            )
            response.raise_for_status()
            payload = response.json()
            observations = payload.get("observations", [])
            raw = pd.DataFrame(observations)
            if raw.empty or "date" not in raw.columns or "value" not in raw.columns:
                raise ValueError("응답 데이터가 비어 있습니다.")
            series = pd.Series(
                pd.to_numeric(raw["value"].replace(".", np.nan), errors="coerce").values,
                index=pd.to_datetime(raw["date"]),
                name=name,
            )
            frames.append(series)
        except Exception as exc:
            warnings.append(f"{name} 로드 실패: {exc}")

    if not frames:
        return pd.DataFrame(), warnings

    macro = pd.concat(frames, axis=1).sort_index().ffill()
    macro["HY_OAS_Z"] = safe_zscore(macro["HY_OAS"])
    return macro, warnings


@cached(cache=_yf_cache, lock=_yf_lock, key=_yf_cache_key)
def fetch_yfinance_series(
    ticker: str,
    start_date: pd.Timestamp,
    preferred_columns: list[str],
) -> tuple[pd.Series, list[str]]:
    if yf is None:
        return pd.Series(dtype=float), [f"yfinance가 설치되지 않아 {ticker} 데이터를 불러올 수 없습니다."]

    try:
        data = yf.download(
            ticker,
            period="max",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=20,
        )
    except Exception as exc:
        return pd.Series(dtype=float), [f"{ticker} 로드 실패: {exc}"]

    if data.empty:
        return pd.Series(dtype=float), [f"{ticker} 데이터가 비어 있습니다."]

    series = coerce_series(data, preferred_columns=preferred_columns)
    series = series.dropna().sort_index()
    series = series.loc[series.index >= start_date]
    if series.empty:
        return pd.Series(dtype=float), [f"{ticker} 데이터가 선택한 기간에 없습니다."]
    series.name = ticker
    return series, []


@cached(cache=_ppr_cache, lock=_ppr_lock)
def fetch_ppr_series(start_date: pd.Timestamp) -> tuple[pd.Series, list[str]]:
    shyg, warnings = fetch_yfinance_series("SHYG", start_date, ["Adj Close", "Close", "SHYG"])
    if shyg.empty:
        return pd.Series(dtype=float), warnings

    shyg = shyg.dropna().sort_index().resample("ME").last().ffill()
    rank = shyg.rolling(12, min_periods=6).rank(pct=True)
    ppr = 1 - rank
    if isinstance(ppr, pd.DataFrame):
        ppr = ppr.squeeze()
    ppr.name = "PPR"
    return ppr, []


def fetch_agg_series(start_date: pd.Timestamp) -> tuple[pd.Series, list[str]]:
    return fetch_yfinance_series("AGG", start_date, ["Adj Close", "Close", "AGG"])


def load_macro_data(
    start_date: pd.Timestamp,
    api_key: str,
    include_ppr: bool,
) -> tuple[pd.DataFrame, list[str], str]:
    macro, warnings = fetch_fred_series(start_date, api_key)
    ppr_note = "PPR 비활성화"

    if macro.empty:
        return macro, warnings, ppr_note

    agg, agg_warnings = fetch_agg_series(start_date)
    warnings.extend(agg_warnings)
    if not agg.empty:
        macro = macro.join(agg, how="left").ffill()

    if include_ppr:
        ppr, ppr_warnings = fetch_ppr_series(start_date)
        warnings.extend(ppr_warnings)
        if not ppr.empty:
            macro = macro.join(ppr, how="left").ffill()
            ppr_note = "PPR = 1 - SHYG 월말가격 12개월 percentile rank"
        else:
            macro["PPR"] = np.nan
            ppr_note = "PPR 로드 실패"
    else:
        macro["PPR"] = np.nan

    return macro, warnings, ppr_note


# backward-compat alias (dashboard.py가 build_dataset으로 호출)
build_dataset = load_macro_data
# backward-compat alias (fetch_fred_api → fetch_fred_series)
fetch_fred_api = fetch_fred_series
