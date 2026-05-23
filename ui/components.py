from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config import CARD_BG, CARD_BG_LIGHT, CARD_BORDER, CARD_BORDER_LIGHT, REGIME_ALLOCATION
from signals import format_value
from ui.theme import get_theme


def render_hero(date_label: str, regime: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">Bond Signal Board</div>
            <div class="hero-sub">FRED API 기반 신호 대시보드.</div>
            <div class="hero-sub">기준일: {date_label} | 현재 Regime: {regime}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_divider() -> None:
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def render_card(title: str, value: str, status: str, note: str, tone: str, dark: bool = True) -> None:
    bg = (CARD_BG if dark else CARD_BG_LIGHT)[tone]
    border = (CARD_BORDER if dark else CARD_BORDER_LIGHT)[tone]
    st.markdown(
        f"""
        <div class="card" style="background:{bg}; border-color:{border};">
            <div class="card-label">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-status">{status}</div>
            <div class="card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_regime_card(regime_name: str, note: str, risk_score: str, tone: str, dark: bool = True) -> None:
    bg = (CARD_BG if dark else CARD_BG_LIGHT)[tone]
    border = (CARD_BORDER if dark else CARD_BORDER_LIGHT)[tone]
    st.markdown(
        f"""
        <div class="card regime-card" style="background:{bg}; border-color:{border};">
            <div class="card-label">CURRENT REGIME</div>
            <div class="regime-value">{regime_name}</div>
            <div class="card-status">{note}</div>
            <div class="card-note">{risk_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_regime_allocation_guide(regime_code: int | None, dark: bool = True) -> None:
    labels = {
        1: "Regime 1 Very Risk On",
        2: "Regime 2 Risk On",
        3: "Regime 3 Risk Off",
        4: "Regime 4 Very Risk Off",
    }
    if regime_code not in REGIME_ALLOCATION:
        return

    weights = REGIME_ALLOCATION[regime_code]
    allocation = " / ".join(f"{ticker} {weight}%" for ticker, weight in weights if weight > 0)
    with st.container(border=True):
        st.markdown(f"**현재 비중 가이드: {labels.get(regime_code, f'Regime {regime_code}')}**")
        st.caption(f"{allocation} 매수")


def render_yield_panel(title: str, data: dict[str, float], columns_per_row: int = 4) -> None:
    st.markdown(f"**{title}**")
    labels = list(data.keys())
    values = list(data.values())
    for row_start in range(0, len(labels), columns_per_row):
        row_labels = labels[row_start : row_start + columns_per_row]
        row_values = values[row_start : row_start + columns_per_row]
        cols = st.columns(columns_per_row)
        for idx, col in enumerate(cols):
            if idx < len(row_labels):
                with col:
                    st.metric(row_labels[idx], format_value(row_values[idx], "%"))


def render_snapshot_board(title: str, items: list[dict[str, str]], columns_per_row: int = 4) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        for start in range(0, len(items), columns_per_row):
            row = items[start : start + columns_per_row]
            cols = st.columns(columns_per_row)
            for idx, col in enumerate(cols):
                if idx < len(row):
                    item = row[idx]
                    delta_value = item["delta"].replace("chg ", "")
                    delta_float = None if delta_value == "N/A" else delta_value
                    with col:
                        st.metric(
                            item["label"],
                            item["value"],
                            delta=delta_float,
                            delta_color="normal",
                            border=True,
                        )


def render_recent_signal_table(frame: pd.DataFrame, max_height: str = "480px") -> None:
    display = frame.copy()
    if "index" in display.columns:
        display = display.rename(columns={"index": "date"})
    if "date" in display.columns:
        display["date"] = pd.to_datetime(display["date"]).dt.strftime("%Y-%m-%d")
    format_map = {
        "VIX": "{:.2f}",
        "OAS_Z": "{:.4f}",
        "PPR": "{:.4f}",
        "UST_10Y_2Y": "{:.2f}",
    }
    for column, fmt in format_map.items():
        if column in display.columns:
            display[column] = display[column].map(
                lambda x, f=fmt: "N/A" if pd.isna(x) else f.format(x)
            )
    html = display.to_html(index=False, escape=False, classes="recent-table")
    st.markdown(
        f'<div class="recent-table-wrap" style="max-height:{max_height}; overflow-y:auto;">'
        f"{html}</div>",
        unsafe_allow_html=True,
    )


def render_metrics_comparison(port_m: dict[str, float], bm_m: dict[str, float]) -> None:
    def _pct(v: float) -> str:
        return f"{v * 100:.2f}%" if isinstance(v, float) and not np.isnan(v) else "N/A"

    def _ratio(v: float) -> str:
        return f"{v:.3f}" if isinstance(v, float) and not np.isnan(v) else "N/A"

    rows = [
        ("총 수익률",     "total_return",  _pct),
        ("연환산 수익률", "ann_return",    _pct),
        ("연환산 변동성", "ann_vol",       _pct),
        ("샤프 비율",     "sharpe",        _ratio),
        ("소르티노 비율", "sortino",       _ratio),
        ("최대 낙폭 MDD", "max_drawdown",  _pct),
    ]

    table_rows = []
    for label, key, fmt in rows:
        pv = port_m.get(key, float("nan"))
        bv = bm_m.get(key, float("nan"))
        diff = float("nan")
        if isinstance(pv, float) and isinstance(bv, float) and not np.isnan(pv) and not np.isnan(bv):
            diff = pv - bv
        diff_fmt = _pct(diff) if key in ("total_return", "ann_return", "ann_vol", "max_drawdown") else _ratio(diff)
        if not np.isnan(diff):
            diff_fmt = f"+{diff_fmt}" if diff > 0 else diff_fmt
        table_rows.append({"지표": label, "Portfolio": fmt(pv), "AGG": fmt(bv), "차이": diff_fmt})

    st.dataframe(pd.DataFrame(table_rows), hide_index=True, width="stretch", height=250)


def render_portfolio_hero(today_stats: dict, dark: bool = True) -> None:
    t = get_theme(dark)
    port = today_stats.get("Portfolio", {})
    agg  = today_stats.get("AGG", {})

    current_nav  = port.get("current",      0.0)
    daily_change = port.get("daily_change", 0.0)
    daily_pct    = port.get("daily_pct",    float("nan"))
    period_pct   = port.get("period_pct",   float("nan"))
    agg_daily    = agg.get("daily_pct",     float("nan"))
    agg_period   = agg.get("period_pct",    float("nan"))

    alpha = (
        period_pct - agg_period
        if not (np.isnan(period_pct) or np.isnan(agg_period))
        else float("nan")
    )

    def _clr(v: float) -> str:
        if np.isnan(v):
            return sub
        return "#22c55e" if v >= 0 else "#ef4444"

    def _fmt(v: float, suffix: str = "%") -> str:
        if np.isnan(v):
            return "N/A"
        sign = "+" if v >= 0 else ""
        return f"{sign}{v:.2f}{suffix}"

    chg_sign = "+" if daily_change >= 0 else ""
    bg     = t["metric_bg"]
    border = t["metric_border"]
    text   = t["text_primary"]
    sub    = t["text_secondary"]
    thead  = t["thead_bg"]
    ttext  = t["thead_text"]

    html = f"""
    <div class="portfolio-summary" style="display:flex;gap:12px;align-items:stretch;margin-bottom:18px;">
      <div style="flex:1;background:{bg};border:1px solid {border};border-radius:8px;padding:18px 20px;">
        <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:{sub};margin-bottom:8px;">NAV</div>
        <div style="font-size:2rem;font-weight:800;color:{text};line-height:1.15;">
          {current_nav:,.2f}
          <span style="font-size:1rem;font-weight:600;color:{_clr(daily_change)};margin-left:10px;">
            {chg_sign}{daily_change:,.2f} ({_fmt(daily_pct)})
          </span>
        </div>
        <div style="font-size:0.88rem;color:{sub};margin-top:10px;">
          기준 100 &nbsp;|&nbsp; 기간 수익률
          <span style="color:{_clr(period_pct)};font-weight:700;"> {_fmt(period_pct)}</span>
        </div>
      </div>
      <div style="flex:1;background:{bg};border:1px solid {border};border-radius:8px;padding:18px 20px;">
        <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:{sub};margin-bottom:8px;">Portfolio vs AGG</div>
        <table style="width:100%;border-collapse:collapse;font-size:0.93rem;">
          <thead>
            <tr style="background:{thead};">
              <th style="text-align:left;padding:7px 12px;color:{ttext};font-weight:700;border-radius:6px 0 0 0;"></th>
              <th style="text-align:right;padding:7px 12px;color:{ttext};font-weight:700;">당일%</th>
              <th style="text-align:right;padding:7px 12px;color:{ttext};font-weight:700;">기간%</th>
              <th style="text-align:right;padding:7px 12px;color:{ttext};font-weight:700;border-radius:0 6px 0 0;">대비%</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="padding:10px 12px;color:{text};font-weight:700;">Portfolio</td>
              <td style="text-align:right;padding:10px 12px;color:{_clr(daily_pct)};font-weight:600;">{_fmt(daily_pct)}</td>
              <td style="text-align:right;padding:10px 12px;color:{_clr(period_pct)};font-weight:600;">{_fmt(period_pct)}</td>
              <td style="text-align:right;padding:10px 12px;color:{_clr(alpha)};font-weight:700;">{_fmt(alpha)}</td>
            </tr>
            <tr>
              <td style="padding:10px 12px;color:{text};font-weight:700;">AGG</td>
              <td style="text-align:right;padding:10px 12px;color:{_clr(agg_daily)};font-weight:600;">{_fmt(agg_daily)}</td>
              <td style="text-align:right;padding:10px 12px;color:{_clr(agg_period)};font-weight:600;">{_fmt(agg_period)}</td>
              <td style="text-align:right;padding:10px 12px;color:{sub};">—</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
