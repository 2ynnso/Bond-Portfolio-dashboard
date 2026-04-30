from __future__ import annotations

import pandas as pd
import streamlit as st

from config import DEFAULT_THRESHOLDS
from data import build_dataset, get_fred_api_key
from signals import (
    classify_oas_z,
    classify_ppr,
    classify_regime_detailed,
    classify_spread,
    classify_vix,
    compute_regimes,
    format_delta,
    format_signed,
    format_value,
    latest_delta,
    latest_value,
)
from ui import (
    inject_css,
    line_chart,
    regime_history_chart,
    render_card,
    render_hero,
    render_recent_signal_table,
    render_regime_card,
    render_section_divider,
    render_snapshot_board,
    signal_focus_chart,
)

st.set_page_config(page_title="Bond Signal Board", page_icon=":bar_chart:", layout="wide")
inject_css()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Control")
    years = st.slider("조회 기간(년)", 1, 15, 8)
    include_ppr = st.toggle("PPR(SHYG) 포함", value=True)

    with st.expander("Regime 임계값 설정"):
        vix_thresh = st.slider(
            "VIX 임계값 (Very Risk Off)",
            min_value=15.0, max_value=50.0,
            value=DEFAULT_THRESHOLDS["vix"], step=1.0,
        )
        oas_z_thresh = st.slider(
            "OAS Z 임계값 (Risk Off)",
            min_value=-2.0, max_value=2.0,
            value=DEFAULT_THRESHOLDS["oas_z"], step=0.1,
        )
        ppr_low = st.slider(
            "PPR 저점 (Very Risk On)",
            min_value=0.05, max_value=0.45,
            value=DEFAULT_THRESHOLDS["ppr_low"], step=0.05,
        )
        ppr_high = st.slider(
            "PPR 고점 (Very Risk Off)",
            min_value=0.55, max_value=0.95,
            value=DEFAULT_THRESHOLDS["ppr_high"], step=0.05,
        )
        st.caption(f"현재: VIX>{vix_thresh:.0f} | OAS_Z≥{oas_z_thresh:.1f} | PPR<{ppr_low:.2f} or >{ppr_high:.2f}")

    if st.button("데이터 새로고침", type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.caption("로컬 `.env` 또는 Streamlit Cloud `secrets`의 `FRED_API_KEY`를 자동 사용")

# ── API Key ───────────────────────────────────────────────────────────────────
api_key = get_fred_api_key()
if not api_key:
    st.error("`FRED_API_KEY`가 필요합니다. 로컬 `.env` 또는 Streamlit Cloud `secrets`에 설정하세요.")
    st.stop()

# ── Data ──────────────────────────────────────────────────────────────────────
start_date = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)
with st.spinner("FRED API 데이터 불러오는 중..."):
    macro_raw, warnings, ppr_note = build_dataset(start_date, api_key, include_ppr)

for warning in warnings:
    st.warning(warning)

if macro_raw.empty:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()

# regime 계산은 캐시 밖에서 — 임계값이 바뀌면 즉시 반영
macro = compute_regimes(macro_raw, vix_thresh, oas_z_thresh, ppr_low, ppr_high)

latest = macro.dropna(how="all").iloc[-1]
latest_date = macro.index.max().strftime("%Y-%m-%d")
render_hero(latest_date, str(latest["regime"]))

# ── Strategy Regime ───────────────────────────────────────────────────────────
regime_detailed = latest["regime_detailed"] if "regime_detailed" in latest.index else "N/A"
regime_tone, regime_note = classify_regime_detailed(regime_detailed)
render_section_divider()
st.markdown("### Strategy Regime")
risk_score_detail = (
    f"Signals:\n"
    f"• VIX({format_value(latest_value(macro, 'VIX'))}) "
    f"• OAS_Z({format_value(latest_value(macro, 'OAS_Z'))}) "
    f"• PPR({format_value(latest_value(macro, 'PPR'))})"
)
render_regime_card(regime_detailed, regime_note, risk_score_detail, "info")

# ── Key Signal Indicators ─────────────────────────────────────────────────────
vix_tone, vix_status, vix_note = classify_vix(latest_value(macro, "VIX"), vix_thresh)
oas_tone, oas_status, oas_note = classify_oas_z(latest_value(macro, "OAS_Z"), oas_z_thresh)
ppr_tone, ppr_status, ppr_note_short = classify_ppr(latest_value(macro, "PPR"), ppr_low, ppr_high)
spread_tone, spread_status, spread_note = classify_spread(latest_value(macro, "UST_10Y_2Y"))

agg_value = latest_value(macro, "AGG")
agg_delta = latest_delta(macro, "AGG", 1)
agg_note = "Benchmark ETF" if not pd.isna(agg_value) else "Yahoo Finance 응답 실패 또는 비어 있음"

st.markdown("### Key Signal Indicators")
st.markdown("**3가지 위험도 지표 + 벤치마크 ETF**")
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_card("VIX", format_value(latest_value(macro, "VIX")), vix_status, vix_note, vix_tone)
with c2:
    render_card("OAS Z", format_value(latest_value(macro, "OAS_Z")), oas_status, oas_note, oas_tone)
with c3:
    render_card("PPR", format_value(latest_value(macro, "PPR")), ppr_status, ppr_note_short, ppr_tone)
with c4:
    render_card("AGG ETF", format_value(agg_value, "$"), format_signed(agg_delta, "$"), agg_note, "agg")

st.caption(ppr_note)

# ── Treasury Snapshot ─────────────────────────────────────────────────────────
st.markdown("### Treasury Snapshot")
render_snapshot_board(
    "US Treasury Curve",
    [
        {"label": "3M",       "value": format_value(latest_value(macro, "UST_3M"),      "%"), "delta": format_delta(latest_delta(macro, "UST_3M"),      "%")},
        {"label": "2Y",       "value": format_value(latest_value(macro, "UST_2Y"),      "%"), "delta": format_delta(latest_delta(macro, "UST_2Y"),      "%")},
        {"label": "3Y",       "value": format_value(latest_value(macro, "UST_3Y"),      "%"), "delta": format_delta(latest_delta(macro, "UST_3Y"),      "%")},
        {"label": "5Y",       "value": format_value(latest_value(macro, "UST_5Y"),      "%"), "delta": format_delta(latest_delta(macro, "UST_5Y"),      "%")},
        {"label": "7Y",       "value": format_value(latest_value(macro, "UST_7Y"),      "%"), "delta": format_delta(latest_delta(macro, "UST_7Y"),      "%")},
        {"label": "10Y",      "value": format_value(latest_value(macro, "UST_10Y"),     "%"), "delta": format_delta(latest_delta(macro, "UST_10Y"),     "%")},
        {"label": "10Y-2Y",   "value": format_value(latest_value(macro, "UST_10Y_2Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_10Y_2Y"), "%")},
        {"label": "HY Yield", "value": format_value(latest_value(macro, "HY_YIELD"),   "%"), "delta": format_delta(latest_delta(macro, "HY_YIELD"),   "%")},
    ],
)

# ── Signal Change Snapshot ────────────────────────────────────────────────────
st.markdown("### Signal Change Snapshot")
render_snapshot_board(
    "Short-Term Change",
    [
        {"label": "VIX 5d",    "value": format_signed(latest_delta(macro, "VIX")),          "delta": format_delta(latest_delta(macro, "VIX"))},
        {"label": "OAS Z 5d",  "value": format_signed(latest_delta(macro, "OAS_Z")),         "delta": format_delta(latest_delta(macro, "OAS_Z"))},
        {"label": "US 10Y 5d", "value": format_signed(latest_delta(macro, "UST_10Y"), "%"),  "delta": format_delta(latest_delta(macro, "UST_10Y"), "%")},
        {"label": "PPR 1m",    "value": format_signed(latest_delta(macro, "PPR", 1)),         "delta": format_delta(latest_delta(macro, "PPR", 1))},
    ],
)

# ── Signal Focus ──────────────────────────────────────────────────────────────
st.markdown("### Signal Focus")
f1, f2, f3 = st.columns(3)
with f1:
    signal_focus_chart(macro, "VIX",   "VIX",   "#3b82f6", [(vix_thresh, "#dc2626"), (20, "#f59e0b")])
with f2:
    signal_focus_chart(macro, "OAS_Z", "OAS Z", "#3b82f6", [(oas_z_thresh, "#dc2626")])
with f3:
    signal_focus_chart(macro, "PPR",   "PPR",   "#20a464", [(ppr_low, "#dc2626"), (ppr_high, "#20a464")])

# ── Regime History ────────────────────────────────────────────────────────────
st.markdown("### Regime History")
regime_history_chart(macro)

# ── Curve And Credit ──────────────────────────────────────────────────────────
st.markdown("### Curve And Credit")
g1, g2 = st.columns(2)
with g1:
    line_chart(macro, ["UST_3Y", "UST_5Y", "UST_7Y", "UST_10Y"], "US Treasury Curve History", ["#3b82f6", "#22c55e", "#14b8a6", "#0f766e"])
with g2:
    line_chart(macro, ["HY_OAS", "HY_YIELD"], "High Yield Credit", ["#dc2626", "#14b8a6"])

line_chart(macro, ["UST_10Y_2Y"], "Curve Slope History", ["#3b82f6"])

# ── Recent Signal Table ───────────────────────────────────────────────────────
st.subheader("Recent Signal Table")

_total_rows = len(macro)
_row_options = [20, 60, 120, 250, _total_rows]
_row_labels = {20: "20행", 60: "60행", 120: "120행 (약 6개월)", 250: "250행 (약 1년)", _total_rows: f"전체 ({_total_rows}행)"}
n_rows = st.select_slider(
    "표시할 행 수",
    options=_row_options,
    value=60,
    format_func=lambda x: _row_labels.get(x, f"{x}행"),
)

signal_cols = [c for c in ["VIX", "OAS_Z", "PPR", "UST_10Y_2Y", "regime", "regime_detailed"] if c in macro.columns]
signal_history = macro[signal_cols].tail(n_rows).iloc[::-1]  # 최신 데이터가 위로
render_recent_signal_table(signal_history.reset_index(), max_height="520px")

# ── CSV Download ──────────────────────────────────────────────────────────────
st.markdown("---")
csv = macro.to_csv().encode("utf-8")
st.download_button(
    label="CSV 다운로드",
    data=csv,
    file_name=f"bond_signal_{pd.Timestamp.today().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)
