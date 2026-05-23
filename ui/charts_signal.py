from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import REGIME_COLORS, REGIME_LABELS
from ui.theme import get_theme


def line_chart(
    frame: pd.DataFrame,
    columns: list[str],
    title: str,
    colors: list[str],
    dark: bool = True,
) -> None:
    t = get_theme(dark)
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
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[column],
            mode="lines",
            name=column,
            line=dict(width=2.5, color=colors[idx % len(colors)]),
        ))
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
    t = get_theme(dark)
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
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data.values,
        mode="lines",
        name=title,
        line=dict(color=color, width=3),
        fill="tozeroy",
        fillcolor=fill_color,
    ))
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
    t = get_theme(dark)
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
            fig.add_trace(go.Scatter(
                x=agg.index,
                y=agg.values,
                mode="lines",
                name="AGG",
                line=dict(color="#facc15" if dark else "#d97706", width=1.5),
            ))

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
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=color, symbol="square"),
            name=label.replace("Regime ", "R"),
            showlegend=True,
        ))

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


def render_hy_oas_vix_chart(frame: pd.DataFrame, dark: bool = True) -> None:
    t = get_theme(dark)
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
