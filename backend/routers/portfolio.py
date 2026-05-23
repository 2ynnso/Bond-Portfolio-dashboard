from __future__ import annotations

import math

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from backend.schemas import (
    AppendTradeRequest,
    AppendTradeResponse,
    IntradayResponse,
    IntradayRow,
    MetricsDict,
    MetricsResponse,
    NavResponse,
    NavRow,
    PositionRow,
    PositionsResponse,
    TodayStatsItem,
    TodayStatsResponse,
    TradeRow,
    TradesResponse,
)
from portfolio import (
    build_intraday_portfolio_return,
    build_position_summary,
    compute_metrics,
    compute_today_stats,
)
from utils.trade_ledger import (
    append_trade,
    compute_twr_nav,
    is_gsheets_configured,
    load_trades,
    trades_to_positions,
)

router = APIRouter()


def _safe(v) -> float | None:
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except Exception:
        return None


def _check_sheets():
    if not is_gsheets_configured():
        raise HTTPException(status_code=503, detail="Google Sheets not configured")


@router.get("/portfolio/nav", response_model=NavResponse)
def get_portfolio_nav():
    _check_sheets()
    trades = load_trades()
    if trades.empty:
        return NavResponse(nav=[], warnings=["No trades found"])

    twr_nav, warns = compute_twr_nav(trades)
    if twr_nav.empty:
        return NavResponse(nav=[], warnings=warns)

    rows: list[NavRow] = []
    for ts, row in twr_nav.iterrows():
        rows.append(NavRow(
            date=ts.strftime("%Y-%m-%d"),
            Portfolio=_safe(row.get("TWR_NAV")),
            AGG=_safe(row.get("AGG")),
        ))
    return NavResponse(nav=rows, warnings=warns)


@router.get("/portfolio/positions", response_model=PositionsResponse)
def get_positions():
    _check_sheets()
    trades = load_trades()
    if trades.empty:
        return PositionsResponse(positions=[], warnings=["No trades found"])

    positions_list = trades_to_positions(trades)
    start_ts = pd.Timestamp(trades["date"].min())
    summary_df, warns = build_position_summary(positions_list, start_ts)
    if summary_df.empty:
        return PositionsResponse(positions=[], warnings=warns)

    col_map = {
        "티커": "ticker",
        "통화": "currency",
        "매수일": "buy_date",
        "매수가": "buy_price",
        "현재가": "current_price",
        "수량": "shares",
        "매수금액 USD": "amount_usd",
        "평가금액 USD": "value_usd",
        "달러 손익": "pnl_usd",
        "달러 수익률": "ret_pct",
        "투자시작 환율": "fx_at_buy",
        "현재환율": "current_fx",
        "매수금액 KRW": "amount_krw",
        "평가금액 KRW": "value_krw",
        "원화 손익": "pnl_krw",
        "원화 수익률": "krw_ret_pct",
    }
    rows: list[PositionRow] = []
    for _, r in summary_df.iterrows():
        rows.append(PositionRow(
            ticker=str(r.get("티커", "")),
            currency=str(r.get("통화", "USD")),
            buy_date=str(r.get("매수일", "")),
            buy_price=_safe(r.get("매수가")),
            current_price=_safe(r.get("현재가")),
            shares=_safe(r.get("수량")),
            amount_usd=_safe(r.get("매수금액 USD")),
            value_usd=_safe(r.get("평가금액 USD")),
            pnl_usd=_safe(r.get("달러 손익")),
            ret_pct=_safe(r.get("달러 수익률")),
            fx_at_buy=_safe(r.get("투자시작 환율")),
            current_fx=_safe(r.get("현재환율")),
            amount_krw=_safe(r.get("매수금액 KRW")),
            value_krw=_safe(r.get("평가금액 KRW")),
            pnl_krw=_safe(r.get("원화 손익")),
            krw_ret_pct=_safe(r.get("원화 수익률")),
        ))
    return PositionsResponse(positions=rows, warnings=warns)


@router.get("/portfolio/intraday", response_model=IntradayResponse)
def get_intraday():
    _check_sheets()
    trades = load_trades()
    if trades.empty:
        return IntradayResponse(intraday=[])

    positions_list = trades_to_positions(trades)
    df = build_intraday_portfolio_return(positions_list)
    if df.empty:
        return IntradayResponse(intraday=[])

    rows: list[IntradayRow] = []
    for ts, row in df.iterrows():
        rows.append(IntradayRow(
            datetime=str(ts),
            Portfolio=_safe(row.get("Portfolio")),
            AGG=_safe(row.get("AGG")),
        ))
    return IntradayResponse(intraday=rows)


@router.get("/portfolio/metrics", response_model=MetricsResponse)
def get_metrics(rf_pct: float = Query(4.5, ge=0, le=20)):
    _check_sheets()
    trades = load_trades()
    if trades.empty:
        raise HTTPException(status_code=404, detail="No trades found")

    twr_nav, _ = compute_twr_nav(trades)
    if twr_nav.empty:
        raise HTTPException(status_code=404, detail="Could not compute NAV")

    rf = rf_pct / 100
    pf_m = compute_metrics(twr_nav["TWR_NAV"], rf)
    bm_m = compute_metrics(twr_nav["AGG"], rf) if "AGG" in twr_nav.columns else {}

    def _to_model(m: dict) -> MetricsDict:
        return MetricsDict(
            total_return=_safe(m.get("total_return")),
            ann_return=_safe(m.get("ann_return")),
            ann_vol=_safe(m.get("ann_vol")),
            sharpe=_safe(m.get("sharpe")),
            sortino=_safe(m.get("sortino")),
            max_drawdown=_safe(m.get("max_drawdown")),
        )

    return MetricsResponse(portfolio=_to_model(pf_m), benchmark=_to_model(bm_m))


@router.get("/portfolio/today", response_model=TodayStatsResponse)
def get_today_stats():
    _check_sheets()
    trades = load_trades()
    if trades.empty:
        raise HTTPException(status_code=404, detail="No trades found")

    twr_nav, _ = compute_twr_nav(trades)
    if twr_nav.empty:
        raise HTTPException(status_code=404, detail="Could not compute NAV")

    nav_df = twr_nav[["TWR_NAV"]].rename(columns={"TWR_NAV": "Portfolio"})
    if "AGG" in twr_nav.columns:
        nav_df["AGG"] = twr_nav["AGG"]

    raw_stats = compute_today_stats(nav_df)
    stats = {
        k: TodayStatsItem(
            current=_safe(v.get("current")),
            daily_change=_safe(v.get("daily_change")),
            daily_pct=_safe(v.get("daily_pct")),
            period_pct=_safe(v.get("period_pct")),
        )
        for k, v in raw_stats.items()
    }
    return TodayStatsResponse(stats=stats)


@router.get("/trades", response_model=TradesResponse)
def get_trades():
    _check_sheets()
    trades = load_trades()
    if trades.empty:
        return TradesResponse(trades=[])

    rows: list[TradeRow] = []
    for _, r in trades.iterrows():
        rows.append(TradeRow(
            date=r["date"].strftime("%Y-%m-%d"),
            ticker=str(r["ticker"]),
            action=str(r["action"]),
            quantity=float(r["quantity"]),
            price_usd=float(r["price_usd"]),
            fx_rate_krw=_safe(r.get("fx_rate_krw")),
        ))
    return TradesResponse(trades=rows)


@router.post("/trades", response_model=AppendTradeResponse)
def post_trade(body: AppendTradeRequest):
    _check_sheets()
    try:
        append_trade(
            body.date,
            body.ticker,
            body.action,
            body.quantity,
            body.price_usd,
            body.fx_rate_krw,
        )
        return AppendTradeResponse(success=True, message="Trade saved")
    except Exception as exc:
        return AppendTradeResponse(success=False, message=str(exc))
