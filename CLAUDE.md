# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the dashboard locally
streamlit run dashboard.py

# Install dependencies
pip install -r requirements.txt

# Set up the virtual environment
python -m venv .venv && source .venv/bin/activate
```

No test suite or linter is configured.

## Architecture

This is a single-page Streamlit app (`dashboard.py`) that renders two tabs: **Signal Board** and **Portfolio Performance**.

### Module responsibilities

| File | Role |
|------|------|
| `config.py` | All constants: FRED series IDs, regime labels/colors, allocation guide, signal thresholds, card color maps (dark + light) |
| `data.py` | Data fetching — FRED REST API (`fetch_fred_api`), yfinance daily prices (`fetch_yfinance_series`, `fetch_agg_series`, `fetch_ppr_series`), assembled in `build_dataset`. All functions are `@st.cache_data` (TTL 1800s except 5m intraday). `get_fred_api_key()` reads from `.env` first, then `st.secrets`. |
| `signals.py` | Pure signal logic — `compute_oas_z` (rolling z-score), `compute_regimes` (hierarchical VIX→OAS_Z→PPR rule), classify helpers, format helpers (`format_value`, `format_delta`, `latest_value`, `latest_delta`) |
| `ui.py` | All Plotly chart builders and Streamlit rendering functions. Dark mode is passed as a `dark: bool` kwarg throughout. CSS injected via `inject_css(dark)`. |
| `portfolio.py` | Portfolio math — `build_position_summary` (current P&L per ticker), `build_intraday_portfolio_return` (5-min intraday), `compute_metrics` (Sharpe, Sortino, MDD, annualized return/vol), `compute_today_stats`. |
| `utils/trade_ledger.py` | Google Sheets trade ledger — `load_trades` / `append_trade` via gspread. `compute_twr_nav` builds a daily TWR NAV series (base=100) by splitting periods at each trade date and geometrically linking sub-period returns. `compute_performance_decomposition` breaks return into price vs FX components. |

### Data flow

```
FRED API ──┐
yfinance ──┤──► data.build_dataset() ──► signals.compute_oas_z()
           │                          ──► signals.compute_regimes()
           │                                │
           │                          macro DataFrame (date index)
           │                                │
           └──────────────────────── dashboard.py ──► ui.py renders

Google Sheets ──► utils.trade_ledger.load_trades()
                ──► compute_twr_nav() ──► portfolio.py metrics ──► ui.py
```

### Regime classification

Sequential rule (not a score): **VIX → OAS_Z → PPR**

1. VIX > threshold → Regime 4 (Very Risk Off)
2. OAS_Z ≥ threshold → Regime 3 (Risk Off)
3. PPR < ppr_low → Regime 1 (Very Risk On)
4. PPR > ppr_high → Regime 4 (Very Risk Off)
5. Otherwise → Regime 2 (Risk On)

Thresholds are sidebar-adjustable; defaults live in `config.DEFAULT_THRESHOLDS`.

### OAS_Z vs HY_OAS_Z

`data.py` computes a static full-period `HY_OAS_Z` inside the cached `fetch_fred_api`. The sidebar-configurable rolling-window `OAS_Z` (12/24/36M) is computed outside the cache in `signals.compute_oas_z()` so window changes don't bust the FRED cache.

## Secrets / environment

- **Local**: `.env` file with `FRED_API_KEY=...`
- **Streamlit Cloud**: `secrets.toml` under `[gcp_service_account]` (service account JSON keys) and `[gsheets]` (with `spreadsheet_id`)
- See `streamlit-secrets.example.toml` for the exact structure

Google Sheets integration is optional — the Portfolio tab shows a setup message if `is_gsheets_configured()` returns false.

## Dark mode

All `ui.py` chart functions accept `dark: bool`. Colors for cards and borders are split into `CARD_BG` / `CARD_BORDER` (dark) and `CARD_BG_LIGHT` / `CARD_BORDER_LIGHT` (light) in `config.py`.
