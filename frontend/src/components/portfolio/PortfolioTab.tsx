import React, { useState } from 'react'
import { useNav, usePositions, useTodayStats } from '../../hooks/usePortfolio'
import NavChart from './NavChart'
import TradeForm from './TradeForm'

interface Props {
  dark?: boolean
}

function fmtPct(v: number | null | undefined) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(2)}%`
}

function fmtNum(v: number | null | undefined, digits = 2) {
  if (v == null) return '—'
  return v.toFixed(digits)
}

export default function PortfolioTab({ dark }: Props) {
  const [tradeOpen, setTradeOpen] = useState(false)
  const { data: navData, isLoading: navLoading } = useNav()
  const { data: posData } = usePositions()
  const { data: statsData } = useTodayStats()

  const bg = dark ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-800'
  const border = dark ? 'border-gray-700' : 'border-gray-200'

  const stats = statsData?.stats?.Portfolio

  return (
    <div className="flex flex-col gap-6">
      {/* Hero stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'NAV', value: fmtNum(stats.current) },
            { label: '당일', value: `${(stats.daily_pct ?? 0) >= 0 ? '+' : ''}${fmtPct(stats.daily_pct != null ? stats.daily_pct / 100 : null)}` },
            { label: '누적', value: `${(stats.period_pct ?? 0) >= 0 ? '+' : ''}${fmtPct(stats.period_pct != null ? stats.period_pct / 100 : null)}` },
          ].map(({ label, value }) => (
            <div key={label} className={`rounded-xl p-4 shadow ${bg} border ${border}`}>
              <p className="text-xs uppercase opacity-60 mb-1">{label}</p>
              <p className="text-2xl font-bold">{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Trade form toggle */}
      <button
        onClick={() => setTradeOpen((v) => !v)}
        className="self-start text-sm px-3 py-1 rounded border border-blue-500 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900"
      >
        {tradeOpen ? '거래 입력 닫기' : '➕ 거래 입력'}
      </button>
      {tradeOpen && <TradeForm dark={dark} />}

      {/* NAV chart */}
      {navLoading ? (
        <div className="opacity-60 text-center py-8">NAV 계산 중...</div>
      ) : navData && navData.nav.length > 0 ? (
        <NavChart data={navData.nav} dark={dark} />
      ) : (
        <div className="opacity-60 text-center py-8">거래 내역이 없거나 NAV 계산에 실패했습니다.</div>
      )}

      {/* Positions table */}
      {posData && posData.positions.length > 0 && (
        <section>
          <h2 className="text-base font-bold mb-2">포지션별 손익</h2>
          <div className="overflow-x-auto">
            <table className={`w-full text-sm ${bg} rounded-xl border ${border}`}>
              <thead>
                <tr className={`border-b ${border} text-xs uppercase opacity-60`}>
                  {['티커', '매수일', '매수가', '현재가', '수량', '달러 손익', '달러 수익률', '원화 수익률'].map((h) => (
                    <th key={h} className="py-2 px-3 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {posData.positions.map((p, i) => (
                  <tr key={i} className={`border-b ${border} hover:opacity-80`}>
                    <td className="py-2 px-3 font-mono font-bold">{p.ticker}</td>
                    <td className="py-2 px-3">{p.buy_date}</td>
                    <td className="py-2 px-3">${fmtNum(p.buy_price)}</td>
                    <td className="py-2 px-3">${fmtNum(p.current_price)}</td>
                    <td className="py-2 px-3">{fmtNum(p.shares, 4)}</td>
                    <td className={`py-2 px-3 ${(p.pnl_usd ?? 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      ${fmtNum(p.pnl_usd)}
                    </td>
                    <td className={`py-2 px-3 ${(p.ret_pct ?? 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {fmtPct(p.ret_pct)}
                    </td>
                    <td className={`py-2 px-3 ${(p.krw_ret_pct ?? 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {fmtPct(p.krw_ret_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
