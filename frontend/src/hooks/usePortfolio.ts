import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchIntraday,
  fetchMetrics,
  fetchNav,
  fetchPositions,
  fetchTodayStats,
  fetchTrades,
  postTrade,
} from '../api/portfolio'
import type { AppendTradeRequest } from '../types'

const STALE = 30 * 60 * 1000

export const useNav = () =>
  useQuery({ queryKey: ['portfolio', 'nav'], queryFn: fetchNav, staleTime: STALE })

export const usePositions = () =>
  useQuery({ queryKey: ['portfolio', 'positions'], queryFn: fetchPositions, staleTime: STALE })

export const useIntraday = () =>
  useQuery({ queryKey: ['portfolio', 'intraday'], queryFn: fetchIntraday, staleTime: 5 * 60 * 1000 })

export const useMetrics = (rf_pct = 4.5) =>
  useQuery({
    queryKey: ['portfolio', 'metrics', rf_pct],
    queryFn: () => fetchMetrics(rf_pct),
    staleTime: STALE,
  })

export const useTodayStats = () =>
  useQuery({ queryKey: ['portfolio', 'today'], queryFn: fetchTodayStats, staleTime: 5 * 60 * 1000 })

export const useTrades = () =>
  useQuery({ queryKey: ['trades'], queryFn: fetchTrades, staleTime: STALE })

export function useAppendTrade() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: AppendTradeRequest) => postTrade(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['trades'] })
      void qc.invalidateQueries({ queryKey: ['portfolio'] })
    },
  })
}
