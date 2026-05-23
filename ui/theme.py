from __future__ import annotations

import streamlit as st

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


def get_theme(dark: bool) -> dict[str, str]:
    return _T_DARK if dark else _T_LIGHT


def inject_css(dark: bool = True) -> None:
    t = get_theme(dark)
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
