from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEFAULT_THRESHOLDS
from data import build_dataset, get_fred_api_key
from portfolio import (
    add_benchmark_nav,
    build_intraday_portfolio_return,
    build_position_summary,
    build_portfolio_nav,
    compute_metrics,
    compute_today_stats,
)
from signals import (
    classify_oas_z,
    classify_ppr,
    classify_regime_detailed,
    classify_vix,
    compute_oas_z,
    compute_regimes,
    format_delta,
    format_signed,
    format_value,
    latest_delta,
    latest_value,
)
from utils.trade_ledger import (
    append_trade,
    compute_performance_decomposition,
    compute_twr_nav,
    is_gsheets_configured,
    load_trades,
)
from ui import (
    inject_css,
    line_chart,
    regime_history_chart,
    render_card,
    render_daily_return_chart,
    render_hero,
    render_intraday_chart,
    render_metrics_comparison,
    render_nav_chart,
    render_portfolio_hero,
    render_recent_signal_table,
    render_regime_allocation_guide,
    render_regime_card,
    render_section_divider,
    render_snapshot_board,
    signal_focus_chart,
)

st.set_page_config(page_title="Bond Signal Board", page_icon=":bar_chart:", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Control")

    dark = st.toggle("🌙 Dark Mode", value=False)
    st.divider()

    years = st.slider("조회 기간(년)", 1, 15, 8)
    include_ppr = st.toggle("PPR(SHYG) 포함", value=True)

    st.markdown("**OAS Z 롤링 윈도우**")
    oas_window = st.radio(
        "OAS Z 롤링 윈도우",
        options=[12, 24, 36],
        index=1,
        format_func=lambda x: f"{x}M",
        horizontal=True,
        label_visibility="collapsed",
    )

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

inject_css(dark)

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

macro_with_oas = compute_oas_z(macro_raw, oas_window)
macro = compute_regimes(macro_with_oas, vix_thresh, oas_z_thresh, ppr_low, ppr_high)

latest = macro.dropna(how="all").iloc[-1]
latest_date = macro.index.max().strftime("%Y-%m-%d")

# ── Hero (탭 바깥에 표시) ─────────────────────────────────────────────────────
render_hero(latest_date, str(latest["regime"]))

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Signal Board", "💰 Portfolio Performance"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Signal Board (기존 콘텐츠)
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    regime_detailed = latest["regime_detailed"] if "regime_detailed" in latest.index else "N/A"
    regime_tone, regime_note = classify_regime_detailed(regime_detailed)
    render_section_divider()
    st.markdown("### Strategy Regime")
    risk_score_detail = (
        f"Signals: "
        f"• VIX({format_value(latest_value(macro, 'VIX'))}) "
        f"• OAS_Z({format_value(latest_value(macro, 'OAS_Z'))}) "
        f"• PPR({format_value(latest_value(macro, 'PPR'))})"
    )
    render_regime_card(regime_detailed, regime_note, risk_score_detail, "info", dark=dark)
    current_regime_code = int(latest["regime_code"]) if not pd.isna(latest.get("regime_code")) else None
    render_regime_allocation_guide(current_regime_code, dark=dark)

    vix_tone, vix_status, vix_note = classify_vix(latest_value(macro, "VIX"), vix_thresh)
    oas_tone, oas_status, oas_note = classify_oas_z(latest_value(macro, "OAS_Z"), oas_z_thresh)
    ppr_tone, ppr_status, ppr_note_short = classify_ppr(latest_value(macro, "PPR"), ppr_low, ppr_high)

    agg_value = latest_value(macro, "AGG")
    agg_delta = latest_delta(macro, "AGG", 1)
    agg_note = "Benchmark ETF" if not pd.isna(agg_value) else "Yahoo Finance 응답 실패"

    st.markdown("### Key Signal Indicators")
    st.markdown("**3가지 위험도 지표 + 벤치마크 ETF**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_card("VIX", format_value(latest_value(macro, "VIX")), vix_status, vix_note, vix_tone, dark=dark)
    with c2:
        render_card("OAS Z", format_value(latest_value(macro, "OAS_Z")), oas_status, oas_note, oas_tone, dark=dark)
    with c3:
        render_card("PPR", format_value(latest_value(macro, "PPR")), ppr_status, ppr_note_short, ppr_tone, dark=dark)
    with c4:
        render_card("AGG ETF", format_value(agg_value, "$"), format_signed(agg_delta, "$"), agg_note, "agg", dark=dark)

    st.caption(ppr_note)

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

    st.markdown("### Signal Change Snapshot")
    render_snapshot_board(
        "Short-Term Change",
        [
            {"label": "VIX 5d",    "value": format_signed(latest_delta(macro, "VIX")),         "delta": format_delta(latest_delta(macro, "VIX"))},
            {"label": "OAS Z 5d",  "value": format_signed(latest_delta(macro, "OAS_Z")),        "delta": format_delta(latest_delta(macro, "OAS_Z"))},
            {"label": "US 10Y 5d", "value": format_signed(latest_delta(macro, "UST_10Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_10Y"), "%")},
            {"label": "PPR 1m",    "value": format_signed(latest_delta(macro, "PPR", 1)),        "delta": format_delta(latest_delta(macro, "PPR", 1))},
        ],
    )

    st.markdown("### Signal Focus")
    f1, f2, f3 = st.columns(3)
    with f1:
        signal_focus_chart(macro, "VIX",   "VIX",   "#3b82f6", [(vix_thresh, "#dc2626"), (20, "#f59e0b")], dark=dark)
    with f2:
        signal_focus_chart(macro, "OAS_Z", "OAS Z", "#3b82f6", [(oas_z_thresh, "#dc2626")], dark=dark)
    with f3:
        signal_focus_chart(macro, "PPR",   "PPR",   "#20a464", [(ppr_low, "#dc2626"), (ppr_high, "#20a464")], dark=dark)

    st.markdown("### Regime History")
    regime_history_chart(macro, dark=dark)

    st.markdown("### Curve And Credit")
    g1, g2 = st.columns(2)
    with g1:
        line_chart(macro, ["UST_3Y", "UST_5Y", "UST_7Y", "UST_10Y"], "US Treasury Curve History", ["#3b82f6", "#22c55e", "#14b8a6", "#0f766e"], dark=dark)
    with g2:
        line_chart(macro, ["HY_OAS", "HY_YIELD"], "High Yield Credit", ["#dc2626", "#14b8a6"], dark=dark)

    line_chart(macro, ["UST_10Y_2Y"], "Curve Slope History", ["#3b82f6"], dark=dark)

    st.subheader("Recent Signal Table")
    _total_rows = len(macro)
    _base = [20, 60, 120, 250]
    _row_options = sorted(set(_base + [_total_rows]))
    _row_labels = {20: "20행", 60: "60행", 120: "약 6개월", 250: "약 1년", _total_rows: f"전체 ({_total_rows}행)"}
    _default = 60 if 60 in _row_options else _row_options[0]
    n_rows = st.select_slider(
        "표시할 행 수",
        options=_row_options,
        value=_default,
        format_func=lambda x: _row_labels.get(x, f"{x}행"),
    )
    signal_cols = [c for c in ["VIX", "OAS_Z", "PPR", "UST_10Y_2Y", "regime", "regime_detailed"] if c in macro.columns]
    signal_history = macro[signal_cols].tail(n_rows).iloc[::-1]
    render_recent_signal_table(signal_history.reset_index(), max_height="520px")

    st.markdown("---")
    csv = macro.to_csv().encode("utf-8")
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name=f"bond_signal_{pd.Timestamp.today().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Portfolio Performance
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Portfolio Performance")
    st.markdown("포지션별 매수일 기준 손익과 AGG 대비 성과지표를 함께 확인합니다.")

    # ── 입력 설정 ─────────────────────────────────────────────────────────────
    col_date, col_rf = st.columns([2, 1])
    with col_date:
        invest_start = st.date_input(
            "투자 시작일",
            value=(pd.Timestamp.today() - pd.DateOffset(years=1)).date(),
            max_value=pd.Timestamp.today().date(),
            help="포트폴리오 NAV 산출 기준일 (이 날의 종가를 매입가로 사용)",
        )
    with col_rf:
        _rf_default = latest_value(macro, "UST_3M")
        rf_pct = st.number_input(
            "무위험수익률 % (Sharpe 계산용)",
            min_value=0.0, max_value=20.0,
            value=float(_rf_default) if not pd.isna(_rf_default) else 4.5,
            step=0.1,
            help="3M UST 최신값 자동 적용 (수동 조정 가능)",
        )

    st.markdown("**포지션 입력**")
    st.caption("통화가 KRW면 투자금액을 원화로 입력하세요. 환율은 투자 시작일의 USD/KRW를 자동 적용합니다.")

    _default_positions = pd.DataFrame({
        "ticker": ["SHYG", "IEF", "TLT"],
        "buy_date": [invest_start, invest_start, invest_start],
        "currency": ["USD", "USD", "USD"],
        "amount": [6000.0, 3000.0, 1000.0],
    })

    positions_df = st.data_editor(
        _default_positions,
        num_rows="dynamic",
        column_config={
            "ticker": st.column_config.TextColumn(
                "티커", help="예: SHYG, IEF, TLT, AGG, HYG, LQD", width="small"
            ),
            "buy_date": st.column_config.DateColumn(
                "매수일", format="YYYY-MM-DD", width="small"
            ),
            "currency": st.column_config.SelectboxColumn(
                "통화", options=["USD", "KRW"], required=True, width="small"
            ),
            "amount": st.column_config.NumberColumn(
                "투자금액", min_value=0.0, format="%.0f", width="small"
            ),
        },
        width="stretch",
    )

    calc_btn = st.button("📈 성과 계산", type="primary")

    # ── 세션 스테이트 초기화 ──────────────────────────────────────────────────
    if "pf_nav" not in st.session_state:
        st.session_state.pf_nav = None
        st.session_state.pf_metrics = None
        st.session_state.bm_metrics = None
        st.session_state.pf_warns = []
        st.session_state.pf_positions = []
        st.session_state.pf_position_summary = None

    # ── 계산 실행 ─────────────────────────────────────────────────────────────
    if calc_btn:
        positions = [
            r for r in positions_df.dropna(subset=["ticker"]).to_dict("records")
            if str(r.get("ticker", "")).strip()
        ]
        if not positions:
            st.warning("포지션을 하나 이상 입력하세요.")
        else:
            with st.spinner("가격 데이터 불러오는 중..."):
                start_ts = pd.Timestamp(invest_start)
                nav_df, warns = build_portfolio_nav(positions, start_ts)
                if not nav_df.empty:
                    nav_df = add_benchmark_nav(nav_df, nav_df.index.min())
                position_summary, summary_warns = build_position_summary(positions, start_ts)
                warns = warns + summary_warns

            st.session_state.pf_nav = nav_df if not nav_df.empty else None
            st.session_state.pf_warns = warns
            st.session_state.pf_positions = positions
            st.session_state.pf_position_summary = position_summary if not position_summary.empty else None

            if not nav_df.empty:
                rf = rf_pct / 100
                st.session_state.pf_metrics = compute_metrics(nav_df["Portfolio"], rf)
                st.session_state.bm_metrics = (
                    compute_metrics(nav_df["AGG"], rf) if "AGG" in nav_df.columns else {}
                )

    # ── 결과 표시 ─────────────────────────────────────────────────────────────
    for w in st.session_state.get("pf_warns", []):
        st.warning(w)

    nav_df = st.session_state.pf_nav
    if nav_df is not None and not nav_df.empty:
        render_section_divider()

        # ① Hero — 현재 NAV / 당일 등락 / 당일·기간·대비% 비교 테이블
        today_stats = compute_today_stats(nav_df)
        render_portfolio_hero(today_stats, dark=dark)

        # ② Intraday Return(%) | Daily NAV — 나란히
        saved_positions = st.session_state.get("pf_positions", [])
        intraday_df = build_intraday_portfolio_return(saved_positions)

        c_intra, c_daily = st.columns(2)
        with c_intra:
            render_intraday_chart(intraday_df, dark=dark)
        with c_daily:
            _bm_cols = [c for c in ["Portfolio", "AGG"] if c in nav_df.columns]
            render_nav_chart(nav_df[_bm_cols], dark=dark, title="Daily NAV", height=320)

        # ③ Daily Return 바차트
        render_daily_return_chart(nav_df["Portfolio"], label="Portfolio", dark=dark)

        render_section_divider()

        # ④ 포지션별 손익
        position_summary = st.session_state.get("pf_position_summary")
        if position_summary is not None and not position_summary.empty:
            st.markdown("### 포지션별 손익")
            st.dataframe(
                position_summary.style.format(
                    {
                        "매수가": "${:,.2f}",
                        "현재가": "${:,.2f}",
                        "수량": "{:,.4f}",
                        "매수금액 USD": "${:,.2f}",
                        "평가금액 USD": "${:,.2f}",
                        "달러 손익": "${:,.2f}",
                        "달러 수익률": "{:.2%}",
                        "투자시작 환율": "{:,.2f}",
                        "현재환율": "{:,.2f}",
                        "매수금액 KRW": "{:,.0f}",
                        "평가금액 KRW": "{:,.0f}",
                        "원화 손익": "{:,.0f}",
                        "원화 수익률": "{:.2%}",
                    }
                ),
                width="stretch",
                height=245,
            )

        # ⑤ 성과지표 비교
        st.markdown("### 성과지표 비교 — Portfolio vs AGG Benchmark")
        render_metrics_comparison(
            st.session_state.pf_metrics or {},
            st.session_state.bm_metrics or {},
        )

        # ⑥ NAV 데이터 테이블
        with st.expander("NAV 데이터 테이블 보기"):
            display_nav = nav_df.copy()
            display_nav.index = display_nav.index.strftime("%Y-%m-%d")
            st.dataframe(
                display_nav.style.format("{:.2f}"),
                width="stretch",
                height=400,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Trade Ledger (Google Sheets 연동 TWR NAV)
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    render_section_divider()
    st.markdown("### 📒 Trade Ledger — TWR NAV (Google Sheets 연동)")

    if not is_gsheets_configured():
        st.info(
            "Google Sheets 연동이 설정되지 않았습니다. "
            "`streamlit-secrets.example.toml`을 참고해 `secrets.toml`에 "
            "`[gcp_service_account]`와 `[gsheets]` 섹션을 추가하세요.",
            icon="ℹ️",
        )
    else:
        # ── 거래 입력 폼 ──────────────────────────────────────────────────────
        with st.expander("➕ 거래 입력", expanded=False):
            with st.form("trade_input_form", clear_on_submit=True):
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    t_date = st.date_input(
                        "거래일",
                        value=pd.Timestamp.today().date(),
                        max_value=pd.Timestamp.today().date(),
                    )
                    t_ticker = st.text_input("티커 (예: SHYG)", placeholder="SHYG").strip().upper()
                with fc2:
                    t_action = st.selectbox("거래 유형", ["BUY", "SELL"])
                    t_qty = st.number_input("수량 (주)", min_value=0.0, step=1.0, format="%.4f")
                with fc3:
                    t_price = st.number_input("매수가 USD", min_value=0.0, step=0.01, format="%.4f")
                    t_fx = st.number_input(
                        "USD/KRW 환율",
                        min_value=0.0,
                        step=1.0,
                        value=1350.0,
                        format="%.2f",
                    )

                submitted = st.form_submit_button("저장", type="primary")
                if submitted:
                    if not t_ticker:
                        st.warning("티커를 입력하세요.")
                    elif t_qty <= 0:
                        st.warning("수량을 입력하세요.")
                    elif t_price <= 0:
                        st.warning("매수가를 입력하세요.")
                    else:
                        ok = append_trade(
                            str(t_date), t_ticker, t_action,
                            t_qty, t_price, t_fx,
                        )
                        if ok:
                            st.success(f"{t_date} {t_action} {t_ticker} {t_qty}주 저장 완료.")
                            st.rerun()

        # ── 거래 내역 테이블 ──────────────────────────────────────────────────
        with st.spinner("Google Sheets에서 거래 데이터 불러오는 중..."):
            trades = load_trades()

        if trades.empty:
            st.info("저장된 거래 내역이 없습니다. 위 폼에서 거래를 입력하세요.")
        else:
            with st.expander("거래 내역 보기", expanded=False):
                display_trades = trades.copy()
                display_trades["date"] = display_trades["date"].dt.strftime("%Y-%m-%d")
                st.dataframe(display_trades, width="stretch", height=300)

            # ── TWR NAV 계산 ──────────────────────────────────────────────────
            with st.spinner("TWR NAV 계산 중..."):
                twr_nav, twr_warns = compute_twr_nav(trades)

            for w in twr_warns:
                st.warning(w)

            if not twr_nav.empty:
                # ─ Hero 지표 ──────────────────────────────────────────────────
                twr = twr_nav["TWR_NAV"].dropna()
                current_nav = float(twr.iloc[-1])
                period_ret = (twr.iloc[-1] / twr.iloc[0] - 1) * 100
                daily_ret = (twr.iloc[-1] / twr.iloc[-2] - 1) * 100 if len(twr) >= 2 else 0.0
                max_dd = float(((twr - twr.cummax()) / twr.cummax()).min()) * 100

                h1, h2, h3, h4 = st.columns(4)
                h1.metric("TWR NAV", f"{current_nav:.2f}", f"{daily_ret:+.2f} (당일)")
                h2.metric("기간 수익률", f"{period_ret:+.2f}%")
                h3.metric("Max Drawdown", f"{max_dd:.2f}%")
                if "IEF" in twr_nav.columns:
                    ief_ret = (twr_nav["IEF"].iloc[-1] / twr_nav["IEF"].iloc[0] - 1) * 100
                    h4.metric("IEF 벤치마크", f"{ief_ret:+.2f}%", f"vs 포트폴리오 {period_ret - ief_ret:+.2f}%p")

                # ─ NAV 차트 ───────────────────────────────────────────────────
                t_dark = dark
                paper_c = "#111111" if t_dark else "#ffffff"
                plot_c = "#000000" if t_dark else "#f8f9fa"
                axis_c = "#888888" if t_dark else "#666666"
                grid_c = "rgba(255,255,255,0.08)" if t_dark else "rgba(0,0,0,0.06)"

                fig = go.Figure()

                # Portfolio TWR NAV
                fig.add_trace(go.Scatter(
                    x=twr_nav.index, y=twr_nav["TWR_NAV"],
                    mode="lines", name="Portfolio TWR NAV",
                    line=dict(color="#3b82f6", width=2),
                ))

                # IEF benchmark
                if "IEF" in twr_nav.columns:
                    fig.add_trace(go.Scatter(
                        x=twr_nav.index, y=twr_nav["IEF"],
                        mode="lines", name="IEF Benchmark",
                        line=dict(color="#f59e0b", width=1.5, dash="dot"),
                    ))

                # Rebalancing date markers
                for td in trades["date"].dt.normalize().unique():
                    if td in twr_nav.index:
                        fig.add_vline(
                            x=td, line_width=1,
                            line_dash="dash", line_color="rgba(34,197,94,0.5)",
                            annotation=dict(
                                text="R",
                                font=dict(size=9, color="#22c55e"),
                            ),
                        )

                fig.update_layout(
                    title="TWR NAV (기준 100) — 수직선: 리밸런싱 발생일",
                    paper_bgcolor=paper_c,
                    plot_bgcolor=plot_c,
                    font=dict(color=axis_c),
                    xaxis=dict(showgrid=True, gridcolor=grid_c, linecolor=axis_c),
                    yaxis=dict(showgrid=True, gridcolor=grid_c, linecolor=axis_c),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=axis_c)),
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                st.plotly_chart(fig, width="stretch")

                # ─ 성과 분해 테이블 ───────────────────────────────────────────
                decomp = compute_performance_decomposition(trades, twr_nav)
                if not decomp.empty:
                    st.markdown("#### 성과 분해 — 가격 수익률 / 환율 효과")
                    st.dataframe(
                        decomp.style.format({
                            "수량": "{:,.4f}",
                            "가격 수익률(USD)": "{:.2%}",
                            "환율 효과(KRW/USD)": "{:.2%}",
                            "교호작용": "{:.2%}",
                            "총 수익률(KRW)": "{:.2%}",
                        }),
                        width="stretch",
                    )
