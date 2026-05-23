from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.theme import get_theme


def render_nav_chart(
    nav_df: pd.DataFrame,
    dark: bool = True,
    title: str = "Daily NAV",
    height: int = 320,
) -> None:
    t = get_theme(dark)
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
        title=dict(text=title, x=0, y=0.97, xanchor="left", font=dict(size=18, color=t["text_primary"])),
        height=height,
        margin=dict(l=18, r=18, t=56, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color=t["text_secondary"])),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"])
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_daily_return_chart(nav: pd.Series, label: str = "Portfolio", dark: bool = True) -> None:
    t = get_theme(dark)
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
        title=dict(text=f"Daily Return — {label} (%)", x=0, y=0.97, xanchor="left", font=dict(size=18, color=t["text_primary"])),
        height=280,
        margin=dict(l=18, r=18, t=56, b=18),
        showlegend=False,
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"], ticksuffix="%")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_intraday_chart(intraday_df: pd.DataFrame, dark: bool = True) -> None:
    t = get_theme(dark)
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
        title=dict(text="Intraday Return (%)", x=0, y=0.97, xanchor="left", font=dict(size=18, color=t["text_primary"])),
        height=320,
        margin=dict(l=18, r=18, t=56, b=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color=t["text_secondary"])),
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, color=t["plot_axis"])
    fig.update_yaxes(gridcolor=t["plot_grid"], color=t["plot_axis"], ticksuffix="%")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_allocation_pie(position_summary: pd.DataFrame, dark: bool = True) -> None:
    t = get_theme(dark)
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
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(color=t["text_secondary"], size=12)),
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


def render_twr_nav_chart(nav_df: pd.DataFrame, trades_df: pd.DataFrame, dark: bool = True) -> None:
    """TWR NAV full chart with AGG overlay and rebalancing vertical lines."""
    t = get_theme(dark)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=nav_df.index, y=nav_df["Portfolio"],
        mode="lines", name="Portfolio (TWR)",
        line=dict(color="#3b82f6", width=2),
    ))
    if "AGG" in nav_df.columns:
        fig.add_trace(go.Scatter(
            x=nav_df.index, y=nav_df["AGG"],
            mode="lines", name="AGG Benchmark",
            line=dict(color="#f59e0b", width=1.5, dash="dot"),
        ))
    for td in trades_df["date"].dt.normalize().unique():
        if td in nav_df.index:
            fig.add_vline(
                x=td.strftime("%Y-%m-%d"),
                line_width=1, line_dash="dash",
                line_color="rgba(34,197,94,0.5)",
            )
    fig.update_layout(
        title="TWR NAV (기준 100) — 수직선: 리밸런싱",
        paper_bgcolor=t["plot_paper"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["plot_axis"]),
        xaxis=dict(showgrid=True, gridcolor=t["plot_grid"], linecolor=t["plot_axis"]),
        yaxis=dict(showgrid=True, gridcolor=t["plot_grid"], linecolor=t["plot_axis"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=t["plot_axis"])),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, width="stretch")
