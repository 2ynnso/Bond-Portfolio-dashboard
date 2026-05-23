from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ── Macro / Signal ────────────────────────────────────────────────────────────

class MacroRow(BaseModel):
    date: str
    VIX: float | None = None
    OAS_Z: float | None = None
    PPR: float | None = None
    HY_OAS: float | None = None
    HY_YIELD: float | None = None
    UST_3M: float | None = None
    UST_2Y: float | None = None
    UST_3Y: float | None = None
    UST_5Y: float | None = None
    UST_7Y: float | None = None
    UST_10Y: float | None = None
    UST_10Y_2Y: float | None = None
    AGG: float | None = None
    regime: float | None = None
    regime_code: float | None = None
    regime_detailed: str | None = None


class MacroLatest(BaseModel):
    date: str
    values: dict[str, Any]


class MacroResponse(BaseModel):
    signals: list[MacroRow]
    latest: MacroLatest
    regime_code: int | None
    warnings: list[str]
    ppr_note: str


# ── Portfolio ─────────────────────────────────────────────────────────────────

class NavRow(BaseModel):
    date: str
    Portfolio: float | None = None
    AGG: float | None = None


class NavResponse(BaseModel):
    nav: list[NavRow]
    warnings: list[str]


class PositionRow(BaseModel):
    ticker: str
    currency: str
    buy_date: str
    buy_price: float | None = None
    current_price: float | None = None
    shares: float | None = None
    amount_usd: float | None = None
    value_usd: float | None = None
    pnl_usd: float | None = None
    ret_pct: float | None = None
    fx_at_buy: float | None = None
    current_fx: float | None = None
    amount_krw: float | None = None
    value_krw: float | None = None
    pnl_krw: float | None = None
    krw_ret_pct: float | None = None


class PositionsResponse(BaseModel):
    positions: list[PositionRow]
    warnings: list[str]


class IntradayRow(BaseModel):
    datetime: str
    Portfolio: float | None = None
    AGG: float | None = None


class IntradayResponse(BaseModel):
    intraday: list[IntradayRow]


class MetricsDict(BaseModel):
    total_return: float | None = None
    ann_return: float | None = None
    ann_vol: float | None = None
    sharpe: float | None = None
    sortino: float | None = None
    max_drawdown: float | None = None


class MetricsResponse(BaseModel):
    portfolio: MetricsDict
    benchmark: MetricsDict


class TodayStatsItem(BaseModel):
    current: float | None = None
    daily_change: float | None = None
    daily_pct: float | None = None
    period_pct: float | None = None


class TodayStatsResponse(BaseModel):
    stats: dict[str, TodayStatsItem]


# ── Trades ────────────────────────────────────────────────────────────────────

class TradeRow(BaseModel):
    date: str
    ticker: str
    action: str
    quantity: float
    price_usd: float
    fx_rate_krw: float | None = None


class TradesResponse(BaseModel):
    trades: list[TradeRow]


class AppendTradeRequest(BaseModel):
    date: str
    ticker: str
    action: str
    quantity: float
    price_usd: float
    fx_rate_krw: float = 1350.0


class AppendTradeResponse(BaseModel):
    success: bool
    message: str = ""
