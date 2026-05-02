from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    CARD_BG,
    CARD_BG_LIGHT,
    CARD_BORDER,
    CARD_BORDER_LIGHT,
    REGIME_ALLOCATION,
    REGIME_COLORS,
    REGIME_LABELS,
)
from signals import format_value

# ── Theme color dicts ─────────────────────────────────────────────────────────
_T_DARK: dict[str, str] = {
    "bg_app":             "#000000",
    "bg_sidebar":         "#111111",
    "sidebar_border":     "#333333",
    "text_primary":       "#ffffff",
    "text_secondary":     "#cccccc",
    "divider":            "linear-gradient(90deg,rgba(255,255,255,0.2),rgba(255,255,255,0.05))",
    "table_wrap_bg":      "#050505",
    "table_wrap_border":  "#2a2a2a",
    "thead_bg":           "#111111",
    "thead_text":         "#d1d5db",
    "thead_border":       "#2a2a2a",
    "tbody_text":         "#f9fafb",
    "tbody_border":       "#1b1b1b",
    "row_odd":            "#080808",
    "row_even":           "#0d0d0d",
    "row_hover":          "#161616",
    "metric_bg":          "rgba(30,30,30,0.5)",
    "metric_border":      "#333333",
    "card_text":          "#ffffff",
    "card_label":         "#aaaaaa",
    "card_note":          "#888888",
    "plot_paper":         "#111111",
    "plot_bg":            "#000000",
    "plot_axis":          "#888888",
    "plot_grid":          "rgba(255,255,255,0.1)",
    "shadow":             "0 12px 24px rgba(0,0,0,0.8)",
}

_T_LIGHT: dict[str, str] = {
    "bg_app":             "#f7f8fb",
    "bg_sidebar":         "#f7f8fb",
    "sidebar_border":     "#e2e8f0",
    "text_primary":       "#111111",
    "text_secondary":     "#4b5563",
    "divider":            "linear-gradient(90deg,rgba(0,0,0,0.12),rgba(0,0,0,0.04))",
    "table_wrap_bg":      "#f7f8fb",
    "table_wrap_border":  "#e5e7eb",
    "thead_bg":           "#f3f4f6",
    "thead_text":         "#374151",
    "thead_border":       "#e5e7eb",
    "tbody_text":         "#111111",
    "tbody_border":       "#efefef",
    "row_odd":            "#f7f8fb",
    "row_even":           "#f7f8fb",
    "row_hover":          "#eef2f7",
    "metric_bg":          "#f7f8fb",
    "metric_border":      "#e2e8f0",
    "card_text":          "#111111",
    "card_label":         "#6b7280",
    "card_note":          "#9ca3af",
    "plot_paper":         "#f7f8fb",
    "plot_bg":            "#f7f8fb",
    "plot_axis":          "#666666",
    "plot_grid":          "rgba(0,0,0,0.07)",
    "shadow":             "0 4px 16px rgba(0,0,0,0.08)",
}


def _t(dark: bool) -> dict[str, str]:
    return _T_DARK if dark else _T_LIGHT


def inject_css(dark: bool = True) -> None:
    t = _t(dark)
    st.markdown(
        f"""
        <style>
        /* ── App / Layout ── */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="stTabs"],
        [data-testid="stTabContent"],
        section.main,
        main {{
            background: {t['bg_app']} !important;
        }}
        .block-container {{
            max-width: 1380px;
            padding-top: 2.3rem;
            padding-bottom: 2rem;
            background: {t['bg_app']} !important;
        }}
        div[data-baseweb="tab-list"],
        div[data-baseweb="tab-panel"] {{
            background: {t['bg_app']} !important;
        }}

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {{
            background: {t['bg_sidebar']} !important;
            border-right: 1px solid {t['sidebar_border']};
        }}
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {{
            color: {t['text_primary']} !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stNumberInput input {{
            background: {t['bg_sidebar']} !important;
            color: {t['text_primary']} !important;
            border-color: {t['sidebar_border']} !important;
        }}

        /* ── Buttons (fix invisible button issue) ── */
        button[kind="secondary"] {{
            background: {t['metric_bg']} !important;
            color: {t['text_primary']} !important;
            border: 1px solid {t['metric_border']} !important;
            border-radius: 8px;
        }}
        button[kind="secondary"]:hover {{
            border-color: {t['text_secondary']} !important;
            opacity: 0.85;
        }}
        button[kind="primary"] {{
            background: #2563eb !important;
            color: #ffffff !important;
            border: 1px solid #2563eb !important;
            border-radius: 8px;
        }}
        button[kind="primary"]:hover {{
            background: #1d4ed8 !important;
        }}

        /* ── Hero ── */
        .hero {{ padding: 10px 0 18px 0; }}
        .hero-title {{
            font-size: 2.55rem;
            font-weight: 800;
            line-height: 1.12;
            margin-bottom: 12px;
            color: {t['text_primary']};
            padding-top: 4px;
        }}
        .hero-sub {{
            font-size: 1rem;
            color: {t['text_secondary']};
            max-width: 760px;
            line-height: 1.45;
            margin-bottom: 2px;
        }}

        /* ── Divider ── */
        .section-divider {{
            height: 1px;
            width: 100%;
            margin: 28px 0 38px 0;
            background: {t['divider']};
        }}

        /* ── Signal Table ── */
        .recent-table-wrap {{
            border: 1px solid {t['table_wrap_border']};
            border-radius: 8px;
            background: {t['table_wrap_bg']};
            overflow-x: auto;
        }}
        .recent-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.98rem;
            background: {t['table_wrap_bg']};
        }}
        .recent-table thead th {{
            position: sticky;
            top: 0;
            background: {t['thead_bg']};
            color: {t['thead_text']};
            font-weight: 700;
            text-align: left;
            padding: 14px 16px;
            border-bottom: 1px solid {t['thead_border']};
            white-space: nowrap;
        }}
        .recent-table tbody td {{
            padding: 14px 16px;
            border-bottom: 1px solid {t['tbody_border']};
            color: {t['tbody_text']};
            white-space: nowrap;
        }}
        .recent-table tbody tr:nth-child(odd) td  {{ background: {t['row_odd']}; }}
        .recent-table tbody tr:nth-child(even) td {{ background: {t['row_even']}; }}
        .recent-table tbody tr:hover td           {{ background: {t['row_hover']}; }}

        /* ── Cards ── */
        .card {{
            border-radius: 8px;
            padding: 18px;
            min-height: 150px;
            border: 1px solid {t['metric_border']};
            box-shadow: none;
        }}
        .card-label {{
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: {t['card_label']};
        }}
        .card-value {{
            margin-top: 10px;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.0;
            color: {t['card_text']};
        }}
        .card-status {{
            margin-top: 12px;
            font-size: 1rem;
            font-weight: 700;
            color: {t['card_text']};
        }}
        .card-note {{
            margin-top: 8px;
            font-size: 0.84rem;
            color: {t['card_note']};
            line-height: 1.4;
        }}
        .regime-card {{
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .regime-value {{
            margin-top: 12px;
            font-size: 2.8rem;
            font-weight: 900;
            line-height: 1.1;
            color: {t['card_text']};
        }}

        /* ── Metric widgets ── */
        [data-testid="stMetric"] {{
            background: {t['metric_bg']} !important;
            border: 1px solid {t['metric_border']} !important;
            border-radius: 8px;
        }}
        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricValue"] {{
            color: {t['text_primary']} !important;
        }}

        /* ── Bordered container (snapshot boards) ── */
        [data-testid="stVerticalBlockBorderWrapper"] > div {{
            border-color: {t['metric_border']} !important;
            background: {t['metric_bg']};
            border-radius: 8px;
        }}

        .allocation-grid {{
            display:grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap:10px;
            margin: 10px 0 2px 0;
        }}
        .allocation-item {{
            border:1px solid {t['metric_border']};
            background:{t['metric_bg']};
            border-radius:8px;
            padding:10px 12px;
        }}
        .allocation-title {{
            color:{t['text_primary']};
            font-weight:700;
            font-size:0.9rem;
            margin-bottom:6px;
        }}
        .allocation-line {{
            color:{t['text_secondary']};
            font-size:0.82rem;
            line-height:1.45;
        }}
        @media (max-width: 900px) {{
            .allocation-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .portfolio-summary {{ flex-direction: column; }}
        }}

        /* ── General text ── */
        h1, h2, h3 {{ color: {t['text_primary']} !important; }}
        p {{ color: {t['text_secondary']}; }}

        /* ── DataFrame ── */
        .stDataFrame {{ background: {t['metric_bg']}; border: 1px solid {t['metric_border']}; }}
        table {{ color: {t['tbody_text']}; }}
        th {{ color: {t['thead_text']} !important; background: {t['thead_bg']} !important; }}
        td {{ color: {t['tbody_text']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def line_chart(
    frame: pd.DataFrame,
    columns: list[str],
    title: str,
    colors: list[str],
    dark: bool = True,
) -> None:
    t = _t(dark)
    selected = [c for c in columns if c in frame.columns]
    if not selected:
        st.info(f"{title} 데이터가 없습니다.")
        return

    data = frame[selected].copy()
    for column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(how="all")
    if data.empty:
        st.info(f"{title} 데이터가 없습니다.")
        return

    fig = go.Figure()
    for idx, column in enumerate(data.columns):
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[column],
                mode="lines",
                name=column,
                line=dict(width=2.5, color=colors[idx % len(colors)]),
            )
        )
    fig.update_layout(
        title=dict(text=title, x=0, y=0.96, xanchor="left", yanchor="top", font=dict(size=20, color=t["text_primary"])),
        height=340,
        margin=dict(l=18, r=18, t=128, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.28, xanchor="left", x=0, font=dict(size=11, color=t["text_secondary"])),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"])
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def signal_focus_chart(
    frame: pd.DataFrame,
    column: str,
    title: str,
    color: str,
    thresholds: list[tuple[float, str]],
    lookback: int = 260,
    dark: bool = True,
) -> None:
    t = _t(dark)
    if column not in frame.columns:
        st.info(f"{title} 데이터가 없습니다.")
        return

    data = pd.to_numeric(frame[column], errors="coerce").dropna().tail(lookback)
    if data.empty:
        st.info(f"{title} 데이터가 없습니다.")
        return

    fill_color = "rgba(59,130,246,0.08)"
    if color == "#20a464":
        fill_color = "rgba(32,164,100,0.08)"
    elif color == "#dc2626":
        fill_color = "rgba(220,38,38,0.08)"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data.values,
            mode="lines",
            name=title,
            line=dict(color=color, width=3),
            fill="tozeroy",
            fillcolor=fill_color,
        )
    )
    for level, dash_color in thresholds:
        fig.add_hline(y=level, line_dash="dash", line_color=dash_color, line_width=1.4)

    fig.update_layout(
        title=title,
        title_font=dict(size=18, color=t["text_primary"]),
        height=240,
        margin=dict(l=14, r=14, t=56, b=10),
        showlegend=False,
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"])
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def regime_history_chart(frame: pd.DataFrame, dark: bool = True) -> None:
    t = _t(dark)
    if "regime_code" not in frame.columns:
        st.info("Regime 데이터가 없습니다.")
        return

    data = frame[["regime_code"]].copy()
    data["regime_code"] = pd.to_numeric(data["regime_code"], errors="coerce")
    data = data.dropna()
    if data.empty:
        st.info("Regime 데이터가 없습니다.")
        return

    fig = go.Figure()

    if "AGG" in frame.columns:
        agg = pd.to_numeric(frame["AGG"], errors="coerce").dropna()
        if not agg.empty:
            fig.add_trace(
                go.Scatter(
                    x=agg.index,
                    y=agg.values,
                    mode="lines",
                    name="AGG",
                    line=dict(color="#facc15" if dark else "#d97706", width=1.5),
                )
            )

    periods: list[tuple] = []
    prev_regime: int | None = None
    period_start = None
    for idx, row in data.iterrows():
        current = int(row["regime_code"])
        if current != prev_regime:
            if prev_regime is not None and period_start is not None:
                periods.append((period_start, idx, prev_regime))
            period_start = idx
            prev_regime = current
    if prev_regime is not None and period_start is not None:
        periods.append((period_start, data.index[-1], prev_regime))

    for start, end, regime in periods:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor=REGIME_COLORS.get(regime, "rgba(100,100,100,0.1)"),
            layer="below",
            line_width=0,
        )

    for code, label in REGIME_LABELS.items():
        color = REGIME_COLORS[code].replace("0.18", "0.7").replace("0.15", "0.7")
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=10, color=color, symbol="square"),
                name=label.replace("Regime ", "R"),
                showlegend=True,
            )
        )

    fig.update_layout(
        title=dict(text="Regime History", x=0, y=0.97, xanchor="left", font=dict(size=20, color=t["text_primary"])),
        height=320,
        margin=dict(l=18, r=18, t=56, b=18),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11, color=t["text_secondary"])),
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"])
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ── Portfolio Performance ──────────────────────────────────────────────────────

def render_nav_chart(
    nav_df: pd.DataFrame,
    dark: bool = True,
    title: str = "Daily NAV",
    height: int = 320,
) -> None:
    t = _t(dark)
    palette = {
        "Portfolio": "#3b82f6",
        "AGG": "#facc15" if dark else "#d97706",
    }
    extra = ["#22c55e", "#dc2626", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]
    extra_idx = 0

    fig = go.Figure()
    for col in nav_df.columns:
        color = palette.get(col)
        if color is None:
            color = extra[extra_idx % len(extra)]
            extra_idx += 1
        is_portfolio = col == "Portfolio"
        fig.add_trace(go.Scatter(
            x=nav_df.index,
            y=nav_df[col],
            mode="lines",
            name=col,
            line=dict(width=3 if is_portfolio else 1.8, color=color),
            opacity=1.0 if is_portfolio else 0.75,
        ))

    fig.add_hline(y=100, line_dash="dot", line_color="rgba(128,128,128,0.35)", line_width=1)

    fig.update_layout(
        title=dict(
            text=title,
            x=0, y=0.97, xanchor="left",
            font=dict(size=18, color=t["text_primary"]),
        ),
        height=height,
        margin=dict(l=18, r=18, t=56, b=18),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color=t["text_secondary"]),
        ),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"])
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_daily_return_chart(nav: pd.Series, label: str = "Portfolio", dark: bool = True) -> None:
    t = _t(dark)
    ret = nav.pct_change().dropna() * 100
    colors = ["#22c55e" if v >= 0 else "#ef4444" for v in ret.values]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ret.index,
        y=ret.values,
        name=label,
        marker_color=colors,
        marker_line_width=0,
    ))
    fig.add_hline(y=0, line_color="rgba(128,128,128,0.4)", line_width=1)

    fig.update_layout(
        title=dict(
            text=f"Daily Return — {label} (%)",
            x=0, y=0.97, xanchor="left",
            font=dict(size=18, color=t["text_primary"]),
        ),
        height=280,
        margin=dict(l=18, r=18, t=56, b=18),
        showlegend=False,
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"], ticksuffix="%")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_portfolio_hero(today_stats: dict, dark: bool = True) -> None:
    t = _t(dark)
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


def render_intraday_chart(intraday_df: pd.DataFrame, dark: bool = True) -> None:
    t = _t(dark)
    if intraday_df.empty:
        st.info("장중 데이터 없음 (미국 ETF 거래시간 외 또는 장 마감 후)")
        return

    palette = {"Portfolio": "#3b82f6", "AGG": "#facc15" if dark else "#d97706"}
    extra = ["#22c55e", "#dc2626", "#8b5cf6"]
    extra_idx = 0

    fig = go.Figure()
    for col in intraday_df.columns:
        color = palette.get(col)
        if color is None:
            color = extra[extra_idx % len(extra)]
            extra_idx += 1
        fig.add_trace(go.Scatter(
            x=intraday_df.index,
            y=intraday_df[col],
            mode="lines",
            name=col,
            line=dict(width=2.5 if col == "Portfolio" else 1.8, color=color),
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(128,128,128,0.4)", line_width=1)

    fig.update_layout(
        title=dict(
            text="Intraday Return (%)",
            x=0, y=0.97, xanchor="left",
            font=dict(size=18, color=t["text_primary"]),
        ),
        height=320,
        margin=dict(l=18, r=18, t=56, b=18),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color=t["text_secondary"]),
        ),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"], ticksuffix="%")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_metrics_comparison(
    port_m: dict[str, float],
    bm_m: dict[str, float],
) -> None:
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
        table_rows.append(
            {
                "지표": label,
                "Portfolio": fmt(pv),
                "AGG": fmt(bv),
                "차이": diff_fmt,
            }
        )

    st.dataframe(
        pd.DataFrame(table_rows),
        hide_index=True,
        width="stretch",
        height=250,
    )


def render_hy_oas_vix_chart(frame: pd.DataFrame, dark: bool = True) -> None:
    t = _t(dark)
    oas = pd.to_numeric(frame.get("HY_OAS"), errors="coerce").dropna() if "HY_OAS" in frame.columns else pd.Series(dtype=float)
    vix = pd.to_numeric(frame.get("VIX"),    errors="coerce").dropna() if "VIX"    in frame.columns else pd.Series(dtype=float)

    if oas.empty and vix.empty:
        st.info("HY OAS / VIX 데이터가 없습니다.")
        return

    fig = go.Figure()

    if not oas.empty:
        fig.add_trace(go.Scatter(
            x=oas.index, y=oas.values,
            name="HY OAS (%)",
            mode="lines",
            line=dict(color="#3b82f6", width=2.5),
            yaxis="y1",
        ))

    if not vix.empty:
        fig.add_trace(go.Scatter(
            x=vix.index, y=vix.values,
            name="VIX",
            mode="lines",
            line=dict(color="#22c55e", width=2.5),
            yaxis="y2",
        ))

    btn_style = dict(
        bgcolor=t["plot_paper"],
        bordercolor=t["plot_axis"],
        font=dict(color=t["text_secondary"], size=11),
        activecolor="#3b82f6",
    )

    fig.update_layout(
        title=dict(
            text="HY OAS vs VIX",
            x=0, y=0.97, xanchor="left", yanchor="top",
            font=dict(size=20, color=t["text_primary"]),
        ),
        height=400,
        margin=dict(l=18, r=60, t=80, b=60),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        legend=dict(
            orientation="h", yanchor="bottom", y=1.08,
            xanchor="left", x=0,
            font=dict(size=11, color=t["text_secondary"]),
        ),
        yaxis=dict(
            title=dict(text="HY OAS (%)", font=dict(color="#3b82f6", size=12)),
            tickfont=dict(color="#3b82f6"),
            gridcolor=t["plot_grid"],
            color=t["plot_axis"],
            side="left",
        ),
        yaxis2=dict(
            title=dict(text="VIX", font=dict(color="#22c55e", size=12)),
            tickfont=dict(color="#22c55e"),
            overlaying="y",
            side="right",
            showgrid=False,
            color=t["plot_axis"],
        ),
        xaxis=dict(
            showgrid=False,
            color=t["plot_axis"],
            rangeselector=dict(
                buttons=[
                    dict(count=1,  label="1M",  step="month", stepmode="backward"),
                    dict(count=3,  label="3M",  step="month", stepmode="backward"),
                    dict(count=6,  label="6M",  step="month", stepmode="backward"),
                    dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
                    dict(count=2,  label="2Y",  step="year",  stepmode="backward"),
                    dict(step="all", label="ALL"),
                ],
                **btn_style,
            ),
            rangeslider=dict(
                visible=True,
                thickness=0.07,
                bgcolor=t["plot_paper"],
                bordercolor=t["plot_axis"],
                borderwidth=1,
            ),
            type="date",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_allocation_pie(position_summary: pd.DataFrame, dark: bool = True) -> None:
    t = _t(dark)
    df = position_summary[["티커", "평가금액 USD"]].copy()
    df = df[df["평가금액 USD"] > 0].dropna()
    if df.empty:
        return

    total = df["평가금액 USD"].sum()
    df["비중"] = df["평가금액 USD"] / total * 100

    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6", "#f97316", "#dc2626"]

    fig = go.Figure(go.Pie(
        labels=df["티커"],
        values=df["평가금액 USD"],
        customdata=df["비중"],
        texttemplate="%{label}<br>%{customdata:.1f}%",
        textposition="inside",
        hovertemplate="%{label}<br>평가금액: $%{value:,.0f}<br>비중: %{customdata:.1f}%<extra></extra>",
        marker=dict(colors=colors[:len(df)], line=dict(color=t["plot_paper"], width=2)),
        hole=0.45,
    ))

    fig.update_layout(
        title=dict(text="포트폴리오 비중", font=dict(color=t["text_primary"], size=15), x=0.5),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text_primary"]),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02,
            y=0.5,
            font=dict(color=t["text_secondary"], size=12),
        ),
        margin=dict(l=10, r=120, t=50, b=10),
        height=320,
        annotations=[dict(
            text=f"${total:,.0f}",
            x=0.5, y=0.5,
            font=dict(size=14, color=t["text_primary"]),
            showarrow=False,
        )],
    )

    st.plotly_chart(fig, use_container_width=True)
