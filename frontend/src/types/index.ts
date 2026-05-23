// ── Macro / Signal ────────────────────────────────────────────────────────────

export interface MacroRow {
  date: string
  VIX?: number | null
  OAS_Z?: number | null
  PPR?: number | null
  HY_OAS?: number | null
  HY_YIELD?: number | null
  UST_3M?: number | null
  UST_2Y?: number | null
  UST_3Y?: number | null
  UST_5Y?: number | null
  UST_7Y?: number | null
  UST_10Y?: number | null
  UST_10Y_2Y?: number | null
  AGG?: number | null
  regime?: number | null
  regime_code?: number | null
  regime_detailed?: string | null
}

export interface MacroLatest {
  date: string
  values: Record<string, number | string | null>
}

export interface MacroResponse {
  signals: MacroRow[]
  latest: MacroLatest
  regime_code: number | null
  warnings: string[]
  ppr_note: string
}

export interface MacroParams {
  years?: number
  oas_window?: number
  vix_thresh?: number
  oas_z_thresh?: number
  ppr_low?: number
  ppr_high?: number
  include_ppr?: boolean
}

// ── Portfolio ─────────────────────────────────────────────────────────────────

export interface NavRow {
  date: string
  Portfolio?: number | null
  AGG?: number | null
}

export interface NavResponse {
  nav: NavRow[]
  warnings: string[]
}

export interface PositionRow {
  ticker: string
  currency: string
  buy_date: string
  buy_price?: number | null
  current_price?: number | null
  shares?: number | null
  amount_usd?: number | null
  value_usd?: number | null
  pnl_usd?: number | null
  ret_pct?: number | null
  fx_at_buy?: number | null
  current_fx?: number | null
  amount_krw?: number | null
  value_krw?: number | null
  pnl_krw?: number | null
  krw_ret_pct?: number | null
}

export interface PositionsResponse {
  positions: PositionRow[]
  warnings: string[]
}

export interface IntradayRow {
  datetime: string
  Portfolio?: number | null
  AGG?: number | null
}

export interface IntradayResponse {
  intraday: IntradayRow[]
}

export interface MetricsDict {
  total_return?: number | null
  ann_return?: number | null
  ann_vol?: number | null
  sharpe?: number | null
  sortino?: number | null
  max_drawdown?: number | null
}

export interface MetricsResponse {
  portfolio: MetricsDict
  benchmark: MetricsDict
}

export interface TodayStatsItem {
  current?: number | null
  daily_change?: number | null
  daily_pct?: number | null
  period_pct?: number | null
}

export interface TodayStatsResponse {
  stats: Record<string, TodayStatsItem>
}

// ── Trades ────────────────────────────────────────────────────────────────────

export interface TradeRow {
  date: string
  ticker: string
  action: string
  quantity: number
  price_usd: number
  fx_rate_krw?: number | null
}

export interface TradesResponse {
  trades: TradeRow[]
}

export interface AppendTradeRequest {
  date: string
  ticker: string
  action: string
  quantity: number
  price_usd: number
  fx_rate_krw?: number
}

export interface AppendTradeResponse {
  success: boolean
  message?: string
}
