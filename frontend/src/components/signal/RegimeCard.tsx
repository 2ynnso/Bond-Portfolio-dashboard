import React from 'react'

const REGIME_COLORS: Record<number, string> = {
  1: 'bg-green-500',
  2: 'bg-blue-500',
  3: 'bg-orange-500',
  4: 'bg-red-600',
}

interface RegimeCardProps {
  regimeCode: number | null
  regimeDetailed: string | null
  signals: { label: string; value: string | number | null | undefined }[]
  dark?: boolean
}

export default function RegimeCard({ regimeCode, regimeDetailed, signals, dark }: RegimeCardProps) {
  const colorClass = regimeCode ? (REGIME_COLORS[regimeCode] ?? 'bg-gray-500') : 'bg-gray-500'
  const cardBg = dark ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-800'

  return (
    <div className={`rounded-xl p-4 shadow ${cardBg} border ${dark ? 'border-gray-700' : 'border-gray-200'}`}>
      <div className="flex items-center gap-3 mb-3">
        <span className={`inline-block w-3 h-3 rounded-full ${colorClass}`} />
        <span className="font-bold text-lg">{regimeDetailed ?? 'N/A'}</span>
      </div>
      <div className="flex flex-wrap gap-3 text-sm">
        {signals.map(({ label, value }) => (
          <span key={label} className={`px-2 py-1 rounded ${dark ? 'bg-gray-700' : 'bg-gray-100'}`}>
            {label}: <strong>{value != null ? String(value) : '—'}</strong>
          </span>
        ))}
      </div>
    </div>
  )
}
