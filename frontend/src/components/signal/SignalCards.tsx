import React from 'react'

interface SignalCardProps {
  label: string
  value: string
  subLabel?: string
  note?: string
  tone?: 'warning' | 'danger' | 'ok' | 'agg' | 'neutral'
  dark?: boolean
}

const TONE_COLORS: Record<string, string> = {
  warning: 'border-yellow-400',
  danger: 'border-red-500',
  ok: 'border-green-500',
  agg: 'border-blue-500',
  neutral: 'border-gray-400',
}

export function SignalCard({ label, value, subLabel, note, tone = 'neutral', dark }: SignalCardProps) {
  const border = TONE_COLORS[tone] ?? 'border-gray-400'
  const bg = dark ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-800'

  return (
    <div className={`rounded-xl p-4 shadow border-l-4 ${border} ${bg}`}>
      <p className="text-xs uppercase tracking-wide opacity-60 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {subLabel && <p className="text-sm mt-1 opacity-80">{subLabel}</p>}
      {note && <p className="text-xs mt-2 opacity-60">{note}</p>}
    </div>
  )
}

interface SignalCardsRowProps {
  vix?: number | null
  oasZ?: number | null
  ppr?: number | null
  agg?: number | null
  aggDelta?: number | null
  dark?: boolean
}

function fmt(v: number | null | undefined, suffix = ''): string {
  if (v == null) return '—'
  return v.toFixed(2) + suffix
}

export default function SignalCardsRow({ vix, oasZ, ppr, agg, aggDelta, dark }: SignalCardsRowProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <SignalCard
        label="VIX"
        value={fmt(vix)}
        tone={vix != null && vix > 25 ? 'danger' : vix != null && vix > 20 ? 'warning' : 'ok'}
        dark={dark}
      />
      <SignalCard
        label="OAS Z"
        value={fmt(oasZ)}
        tone={oasZ != null && oasZ >= 1 ? 'danger' : 'ok'}
        dark={dark}
      />
      <SignalCard
        label="PPR"
        value={fmt(ppr)}
        tone={ppr != null && ppr > 0.8 ? 'danger' : ppr != null && ppr < 0.2 ? 'ok' : 'neutral'}
        dark={dark}
      />
      <SignalCard
        label="AGG ETF"
        value={fmt(agg, ' $')}
        subLabel={aggDelta != null ? `${aggDelta >= 0 ? '+' : ''}${aggDelta.toFixed(2)}` : undefined}
        tone="agg"
        dark={dark}
      />
    </div>
  )
}
