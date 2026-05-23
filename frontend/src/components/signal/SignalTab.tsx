import React from 'react'
import { useMacroData } from '../../hooks/useMacroData'
import type { MacroParams } from '../../types'
import RegimeCard from './RegimeCard'
import SignalCardsRow from './SignalCards'
import { HyOasVixChart, RegimeHistoryChart, TreasuryLineChart } from './MacroChart'

interface Props {
  params: MacroParams
  dark?: boolean
}

export default function SignalTab({ params, dark }: Props) {
  const { data, isLoading, error } = useMacroData(params)

  if (isLoading) {
    return <div className="p-8 text-center opacity-60">FRED API 데이터 불러오는 중...</div>
  }
  if (error || !data) {
    return <div className="p-8 text-center text-red-500">데이터 로드 실패</div>
  }

  const latest = data.latest.values
  const signals = data.signals

  return (
    <div className="flex flex-col gap-6">
      {data.warnings.map((w, i) => (
        <div key={i} className="text-sm text-yellow-600 bg-yellow-50 dark:bg-yellow-900 dark:text-yellow-300 rounded px-3 py-2">{w}</div>
      ))}

      <section>
        <h2 className="text-base font-bold mb-2">Strategy Regime</h2>
        <RegimeCard
          regimeCode={data.regime_code}
          regimeDetailed={latest['regime_detailed'] as string | null}
          signals={[
            { label: 'VIX', value: latest['VIX'] != null ? Number(latest['VIX']).toFixed(2) : '—' },
            { label: 'OAS_Z', value: latest['OAS_Z'] != null ? Number(latest['OAS_Z']).toFixed(2) : '—' },
            { label: 'PPR', value: latest['PPR'] != null ? Number(latest['PPR']).toFixed(2) : '—' },
          ]}
          dark={dark}
        />
      </section>

      <section>
        <h2 className="text-base font-bold mb-2">Key Signal Indicators</h2>
        <SignalCardsRow
          vix={latest['VIX'] as number | null}
          oasZ={latest['OAS_Z'] as number | null}
          ppr={latest['PPR'] as number | null}
          agg={latest['AGG'] as number | null}
          dark={dark}
        />
      </section>

      <HyOasVixChart data={signals} dark={dark} />
      <TreasuryLineChart data={signals} dark={dark} />
      <RegimeHistoryChart data={signals} dark={dark} />

      {data.ppr_note && (
        <p className="text-xs opacity-60">{data.ppr_note}</p>
      )}
    </div>
  )
}
