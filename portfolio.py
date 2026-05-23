from __future__ import annotations

import numpy as np
import pandas as pd

from utils.price_fetcher import fetch_intraday, fetch_price_history

_NAV_BASE = 100
_FX_TICKER = "KRW=X"


def _as_timestamp(value, fallback: pd.Timestamp) -> pd.Timestamp:
    try:
        if pd.isna(value):
            return fallback
    except TypeError:
        pass
    try:
        return pd.Timestamp(value).tz_localize(None)
    except Exception:
        return fallback


def _position_currency(pos: dict) -> str:
    currency = str(pos.get("currency", "USD")).strip().upper()
    return currency if currency in {"USD", "KRW"} else "USD"


def _position_fx(fx_history: pd.Series, fx_date: pd.Timestamp) -> float:
    if fx_history.empty:
        return float("nan")
    fx = fx_history[fx_history.index >= fx_date]
    if fx.empty:
        fx = fx_history
    return float(fx.iloc[0]) if not fx.empty else float("nan")


def _position_amounts(pos: dict, fx_at_buy: float) -> tuple[float, float]:
    amount = float(pos.get("amount", 0.0) or 0.0)
    currency = _position_currency(pos)
    if amount <= 0:
        return 0.0, 0.0
    if currency == "KRW":
        amount_usd = amount / fx_at_buy if fx_at_buy and not np.isnan(fx_at_buy) else 0.0
        return amount_usd, amount
    amount_krw = amount * fx_at_buy if fx_at_buy and not np.isnan(fx_at_buy) else float("nan")
    return amount, amount_krw


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
    clean_positions: list[dict] = []

    start_naive = start_date.tz_localize(None) if start_date.tzinfo else start_date
    buy_dates = [_as_timestamp(pos.get("buy_date"), start_naive) for pos in positions]
    fx_start = min(buy_dates + [start_naive]).strftime("%Y-%m-%d")
    fx_history = fetch_price_history(_FX_TICKER, fx_start)

    for pos in positions:
        tkr = str(pos.get("ticker", "")).strip().upper()
        buy_date = _as_timestamp(pos.get("buy_date"), start_naive)
        fx_at_buy = _position_fx(fx_history, start_naive)
        amt_usd, _ = _position_amounts(pos, fx_at_buy)
        if not tkr or amt_usd <= 0:
            continue
        s = fetch_price_history(tkr, buy_date.strftime("%Y-%m-%d"))
        if s.empty:
            warns.append(f"{tkr}: 가격 데이터를 가져오지 못했습니다.")
            continue
        s = s[s.index >= buy_date]
        if s.empty:
            warns.append(f"{tkr}: 선택한 기간의 데이터가 없습니다.")
            continue
        if tkr not in price_dict or s.index[0] < price_dict[tkr].index[0]:
            price_dict[tkr] = s
        clean_positions.append(
            {
                "ticker": tkr,
                "amount_usd": amt_usd,
                "buy_date": buy_date,
                "first_date": s.index[0],
                "prices": s,
            }
        )

    if not price_dict:
        return pd.DataFrame(), warns

    nav_start = max(pos["first_date"] for pos in clean_positions)
    all_dates = pd.DatetimeIndex(
        sorted(set().union(*[set(pos["prices"][pos["prices"].index >= nav_start].index.tolist()) for pos in clean_positions]))
    )
    if all_dates.empty:
        return pd.DataFrame(), warns + ["포트폴리오 공통 산출 기간을 구성하지 못했습니다."]

    port_val = pd.Series(0.0, index=all_dates)
    any_added = False

    for pos in clean_positions:
        tkr = pos["ticker"]
        amt = pos["amount_usd"]
        prices = pos["prices"]
        p = prices.reindex(all_dates).ffill().bfill()
        buy_prices = prices[prices.index >= pos["buy_date"]]
        init = buy_prices.iloc[0] if not buy_prices.empty else p.iloc[0]
        if pd.isna(init) or init <= 0:
            warns.append(f"{tkr}: 시작일 가격을 확인할 수 없습니다.")
            continue
        port_val += p * (amt / init)
        any_added = True

    if not any_added or port_val.iloc[0] == 0:
        return pd.DataFrame(), warns + ["포트폴리오를 구성하지 못했습니다."]

    nav_df = pd.DataFrame(index=all_dates)
    nav_df["Portfolio"] = port_val / port_val.iloc[0] * _NAV_BASE

    for tkr, prices in price_dict.items():
        p = prices.reindex(all_dates).ffill().bfill()
        nav_df[tkr] = p / p.iloc[0] * _NAV_BASE

    return nav_df, warns


def build_position_summary(
    positions: list[dict],
    fallback_start: pd.Timestamp,
) -> tuple[pd.DataFrame, list[str]]:
    """Compute per-position USD/KRW P&L from each row's buy date."""
    warns: list[str] = []
    start_naive = fallback_start.tz_localize(None) if fallback_start.tzinfo else fallback_start
    buy_dates = [_as_timestamp(pos.get("buy_date"), start_naive) for pos in positions]
    fx_history = fetch_price_history(_FX_TICKER, min(buy_dates + [start_naive]).strftime("%Y-%m-%d"))
    current_fx = float(fx_history.iloc[-1]) if not fx_history.empty else float("nan")

    rows: list[dict] = []
    for pos in positions:
        tkr = str(pos.get("ticker", "")).strip().upper()
        buy_date = _as_timestamp(pos.get("buy_date"), start_naive)
        fx_at_buy = _position_fx(fx_history, start_naive)
        amount_usd, amount_krw = _position_amounts(pos, fx_at_buy)
        if not tkr or amount_usd <= 0:
            continue

        prices = fetch_price_history(tkr, buy_date.strftime("%Y-%m-%d"))
        prices = prices[prices.index >= buy_date]
        if prices.empty:
            warns.append(f"{tkr}: 포지션 손익 계산용 가격 데이터가 없습니다.")
            continue

        buy_price = float(prices.iloc[0])
        current_price = float(prices.iloc[-1])
        shares = amount_usd / buy_price if buy_price > 0 else 0.0
        value_usd = shares * current_price
        pnl_usd = value_usd - amount_usd
        ret_pct = pnl_usd / amount_usd if amount_usd else float("nan")
        value_krw = value_usd * current_fx if not np.isnan(current_fx) else float("nan")
        pnl_krw = value_krw - amount_krw if not np.isnan(value_krw) and not np.isnan(amount_krw) else float("nan")
        krw_ret_pct = pnl_krw / amount_krw if amount_krw and not np.isnan(pnl_krw) else float("nan")

        rows.append(
            {
                "티커": tkr,
                "통화": _position_currency(pos),
                "매수일": prices.index[0].strftime("%Y-%m-%d"),
                "매수가": buy_price,
                "현재가": current_price,
                "수량": shares,
                "매수금액 USD": amount_usd,
                "평가금액 USD": value_usd,
                "달러 손익": pnl_usd,
                "달러 수익률": ret_pct,
                "투자시작 환율": fx_at_buy,
                "현재환율": current_fx,
                "매수금액 KRW": amount_krw,
                "평가금액 KRW": value_krw,
                "원화 손익": pnl_krw,
                "원화 수익률": krw_ret_pct,
            }
        )

    return pd.DataFrame(rows), warns


def add_benchmark_nav(nav_df: pd.DataFrame, start_date: pd.Timestamp) -> pd.DataFrame:
    """Fetch AGG and add as benchmark column (base=100) if not already present."""
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
    nav_df["AGG"] = p / p.iloc[0] * _NAV_BASE
    return nav_df


def build_intraday_portfolio_return(positions: list[dict]) -> pd.DataFrame:
    """
    Compute intraday return % from open for portfolio and AGG.
    Returns DataFrame with columns ["Portfolio", "AGG"] (% from day open).
    """
    valid = [
        pos for pos in positions
        if str(pos.get("ticker", "")).strip() and float(pos.get("amount", 0) or 0) > 0
    ]
    if not valid:
        return pd.DataFrame()

    all_tickers = list(dict.fromkeys(
        [str(p["ticker"]).strip().upper() for p in valid] + ["AGG"]
    ))

    intraday: dict[str, pd.Series] = {}
    for tkr in all_tickers:
        s = fetch_intraday(tkr)
        if not s.empty:
            intraday[tkr] = s

    if not intraday:
        return pd.DataFrame()

    common_idx = None
    for s in intraday.values():
        common_idx = s.index if common_idx is None else common_idx.intersection(s.index)

    if common_idx is None or len(common_idx) < 2:
        return pd.DataFrame()

    result = pd.DataFrame(index=common_idx)

    port_ret = pd.Series(0.0, index=common_idx)
    total_wt = 0.0
    for pos in valid:
        tkr = str(pos["ticker"]).strip().upper()
        amt = float(pos.get("amount", 0) or 0)
        if tkr not in intraday:
            continue
        s = intraday[tkr].reindex(common_idx).ffill()
        port_ret += (s / s.iloc[0] - 1) * 100 * amt
        total_wt += amt

    if total_wt > 0:
        result["Portfolio"] = port_ret / total_wt

    if "AGG" in intraday:
        s = intraday["AGG"].reindex(common_idx).ffill()
        result["AGG"] = (s / s.iloc[0] - 1) * 100

    return result


def compute_today_stats(nav_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Current NAV, daily change, period return for each column."""
    stats: dict[str, dict[str, float]] = {}
    for col in nav_df.columns:
        s = nav_df[col].dropna()
        if len(s) < 2:
            continue
        current = float(s.iloc[-1])
        prev = float(s.iloc[-2])
        first = float(s.iloc[0])
        stats[col] = {
            "current": current,
            "daily_change": current - prev,
            "daily_pct": (current / prev - 1) * 100,
            "period_pct": (current / first - 1) * 100,
        }
    return stats


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
