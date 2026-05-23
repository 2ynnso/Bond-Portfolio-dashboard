import type {
  AppendTradeRequest,
  AppendTradeResponse,
  IntradayResponse,
  MetricsResponse,
  NavResponse,
  PositionsResponse,
  TodayStatsResponse,
  TradesResponse,
} from '../types'
import api from './client'

export const fetchNav = (): Promise<NavResponse> =>
  api.get<NavResponse>('/portfolio/nav').then((r) => r.data)

export const fetchPositions = (): Promise<PositionsResponse> =>
  api.get<PositionsResponse>('/portfolio/positions').then((r) => r.data)

export const fetchIntraday = (): Promise<IntradayResponse> =>
  api.get<IntradayResponse>('/portfolio/intraday').then((r) => r.data)

export const fetchMetrics = (rf_pct = 4.5): Promise<MetricsResponse> =>
  api.get<MetricsResponse>('/portfolio/metrics', { params: { rf_pct } }).then((r) => r.data)

export const fetchTodayStats = (): Promise<TodayStatsResponse> =>
  api.get<TodayStatsResponse>('/portfolio/today').then((r) => r.data)

export const fetchTrades = (): Promise<TradesResponse> =>
  api.get<TradesResponse>('/trades').then((r) => r.data)

export const postTrade = (body: AppendTradeRequest): Promise<AppendTradeResponse> =>
  api.post<AppendTradeResponse>('/trades', body).then((r) => r.data)
