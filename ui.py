from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import CARD_BG, CARD_BORDER, REGIME_COLORS, REGIME_LABELS
from signals import format_value


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #000000;
            color: #ffffff;
        }
        .block-container {max-width: 1380px; padding-top: 2.3rem; padding-bottom: 2rem;}
        [data-testid="stSidebar"] {
            background: #111111;
            border-right: 1px solid #333333;
        }
        .hero { padding: 10px 0 18px 0; }
        .hero-title {
            font-size: 2.55rem;
            font-weight: 800;
            line-height: 1.12;
            margin-bottom: 12px;
            color: #ffffff;
            padding-top: 4px;
        }
        .hero-sub {
            font-size: 1rem;
            color: #cccccc;
            max-width: 760px;
            line-height: 1.45;
            margin-bottom: 2px;
        }
        .section-divider {
            height: 1px;
            width: 100%;
            margin: 34px 0 56px 0;
            background: linear-gradient(90deg, rgba(255,255,255,0.2), rgba(255,255,255,0.1));
        }
        .recent-table-wrap {
            border: 1px solid #2a2a2a;
            border-radius: 18px;
            background: #050505;
            overflow-x: auto;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
        }
        .recent-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            color: #f3f4f6;
            font-size: 0.98rem;
            background: #050505;
        }
        .recent-table thead th {
            position: sticky;
            top: 0;
            background: #111111;
            color: #d1d5db;
            font-weight: 700;
            text-align: left;
            padding: 14px 16px;
            border-bottom: 1px solid #2a2a2a;
            white-space: nowrap;
        }
        .recent-table tbody td {
            padding: 14px 16px;
            border-bottom: 1px solid #1b1b1b;
            color: #f9fafb;
            white-space: nowrap;
        }
        .recent-table tbody tr:nth-child(odd) td { background: #080808; }
        .recent-table tbody tr:nth-child(even) td { background: #0d0d0d; }
        .recent-table tbody tr:hover td { background: #161616; }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div { color: #f3f4f6 !important; }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stNumberInput input {
            background: #111111 !important;
            color: #f9fafb !important;
            border-color: #333333 !important;
        }
        [data-testid="stSidebar"] button { color: #f9fafb !important; }
        .card {
            border-radius: 18px;
            padding: 18px;
            min-height: 150px;
            border: 1px solid #333333;
            box-shadow: 0 12px 24px rgba(0,0,0,0.8);
            background: rgba(0,0,0,0.7);
        }
        .card-label {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #aaaaaa;
        }
        .card-value {
            margin-top: 10px;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.0;
            color: #ffffff;
        }
        .card-status { margin-top: 12px; font-size: 1rem; font-weight: 700; color: #ffffff; }
        .card-note { margin-top: 8px; font-size: 0.84rem; color: #888888; line-height: 1.4; }
        .regime-card { min-height: 200px; display: flex; flex-direction: column; justify-content: space-between; }
        .regime-value { margin-top: 12px; font-size: 2.8rem; font-weight: 900; line-height: 1.1; color: #ffffff; }
        .panel { border-radius: 16px; padding: 14px 16px; border: 1px solid #333333; background: rgba(0,0,0,0.5); }
        h1, h2, h3, p, label, span, div { color: #ffffff; }
        .stMetric { background: rgba(0,0,0,0.3); border: 1px solid #333333; border-radius: 10px; }
        .stDataFrame { background: rgba(0,0,0,0.3); border: 1px solid #333333; }
        [data-testid="stDataFrameContainer"] { color: #ffffff; }
        table { color: #ffffff; }
        th { color: #cccccc; background: rgba(0,0,0,0.5) !important; }
        td { color: #ffffff; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_card(title: str, value: str, status: str, note: str, tone: str) -> None:
    st.markdown(
        f"""
        <div class="card" style="background:{CARD_BG[tone]}; border-color:{CARD_BORDER[tone]};">
            <div class="card-label">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-status">{status}</div>
            <div class="card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_regime_card(regime_name: str, note: str, risk_score: str, tone: str) -> None:
    st.markdown(
        f"""
        <div class="card regime-card" style="background:{CARD_BG[tone]}; border-color:{CARD_BORDER[tone]};">
            <div class="card-label">CURRENT REGIME</div>
            <div class="regime-value">{regime_name}</div>
            <div class="card-status">{note}</div>
            <div class="card-note">{risk_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
                        st.metric(item["label"], item["value"], delta=delta_float, border=True)


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


def line_chart(frame: pd.DataFrame, columns: list[str], title: str, colors: list[str]) -> None:
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
        title=dict(text=title, x=0, y=0.96, xanchor="left", yanchor="top", font=dict(size=20, color="#ffffff")),
        height=340,
        margin=dict(l=18, r=18, t=128, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.28, xanchor="left", x=0, font=dict(size=11, color="#cccccc")),
        paper_bgcolor="#111111",
        plot_bgcolor="#000000",
    )
    fig.update_xaxes(showgrid=False, color="#888888")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", color="#888888")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def signal_focus_chart(
    frame: pd.DataFrame,
    column: str,
    title: str,
    color: str,
    thresholds: list[tuple[float, str]],
    lookback: int = 260,
) -> None:
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
        title_font=dict(size=18, color="#ffffff"),
        height=240,
        margin=dict(l=14, r=14, t=56, b=10),
        showlegend=False,
        paper_bgcolor="#111111",
        plot_bgcolor="#000000",
    )
    fig.update_xaxes(showgrid=False, color="#888888")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", color="#888888")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def regime_history_chart(frame: pd.DataFrame) -> None:
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

    # AGG를 오버레이로 표시
    if "AGG" in frame.columns:
        agg = pd.to_numeric(frame["AGG"], errors="coerce").dropna()
        if not agg.empty:
            fig.add_trace(
                go.Scatter(
                    x=agg.index,
                    y=agg.values,
                    mode="lines",
                    name="AGG",
                    line=dict(color="#facc15", width=1.5),
                )
            )

    # 연속된 동일 regime 구간을 묶어 vrect로 배경색 표시
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
            x0=start,
            x1=end,
            fillcolor=REGIME_COLORS.get(regime, "rgba(100,100,100,0.1)"),
            layer="below",
            line_width=0,
        )

    # 범례용 더미 트레이스
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
        title=dict(text="Regime History", x=0, y=0.97, xanchor="left", font=dict(size=20, color="#ffffff")),
        height=320,
        margin=dict(l=18, r=18, t=56, b=18),
        paper_bgcolor="#111111",
        plot_bgcolor="#000000",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11, color="#cccccc")),
    )
    fig.update_xaxes(showgrid=False, color="#888888")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", color="#888888")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
