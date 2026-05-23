import React from 'react'
import Plot from 'react-plotly.js'
import type { MacroRow } from '../../types'

interface Props {
  data: MacroRow[]
  dark?: boolean
}

const DARK_LAYOUT = {
  paper_bgcolor: '#1f2937',
  plot_bgcolor: '#1f2937',
  font: { color: '#e5e7eb' },
  xaxis: { gridcolor: '#374151' },
  yaxis: { gridcolor: '#374151' },
}

const LIGHT_LAYOUT = {
  paper_bgcolor: '#ffffff',
  plot_bgcolor: '#f9fafb',
  font: { color: '#111827' },
  xaxis: { gridcolor: '#e5e7eb' },
  yaxis: { gridcolor: '#e5e7eb' },
}

export function HyOasVixChart({ data, dark }: Props) {
  const dates = data.map((r) => r.date)
  const theme = dark ? DARK_LAYOUT : LIGHT_LAYOUT

  return (
    <Plot
      data={[
        {
          x: dates,
          y: data.map((r) => r.HY_OAS ?? null),
          name: 'HY OAS',
          type: 'scatter',
          mode: 'lines',
          line: { color: '#dc2626' },
          yaxis: 'y',
        },
        {
          x: dates,
          y: data.map((r) => r.VIX ?? null),
          name: 'VIX',
          type: 'scatter',
          mode: 'lines',
          line: { color: '#3b82f6', dash: 'dot' },
          yaxis: 'y2',
        },
      ]}
      layout={{
        ...theme,
        title: { text: 'HY OAS vs VIX', font: { size: 14 } },
        legend: { x: 1, xanchor: 'right', y: 1 },
        xaxis: { ...theme.xaxis, rangeslider: { visible: true } },
        yaxis: { ...theme.yaxis, title: 'HY OAS (bps)' },
        yaxis2: {
          ...theme.yaxis,
          title: 'VIX',
          overlaying: 'y',
          side: 'right',
        },
        margin: { t: 40, b: 80, l: 60, r: 60 },
        autosize: true,
      }}
      useResizeHandler
      style={{ width: '100%', height: 360 }}
      config={{ displayModeBar: false }}
    />
  )
}

export function TreasuryLineChart({ data, dark }: Props) {
  const dates = data.map((r) => r.date)
  const theme = dark ? DARK_LAYOUT : LIGHT_LAYOUT
  const series = [
    { key: 'UST_3Y' as keyof MacroRow, color: '#3b82f6' },
    { key: 'UST_5Y' as keyof MacroRow, color: '#22c55e' },
    { key: 'UST_7Y' as keyof MacroRow, color: '#14b8a6' },
    { key: 'UST_10Y' as keyof MacroRow, color: '#0f766e' },
  ]

  return (
    <Plot
      data={series.map(({ key, color }) => ({
        x: dates,
        y: data.map((r) => (r[key] as number | null | undefined) ?? null),
        name: String(key),
        type: 'scatter',
        mode: 'lines',
        line: { color },
      }))}
      layout={{
        ...theme,
        title: { text: 'US Treasury Curve History', font: { size: 14 } },
        legend: { x: 0, y: 1 },
        margin: { t: 40, b: 40, l: 50, r: 20 },
        autosize: true,
      }}
      useResizeHandler
      style={{ width: '100%', height: 300 }}
      config={{ displayModeBar: false }}
    />
  )
}

export function RegimeHistoryChart({ data, dark }: Props) {
  const dates = data.map((r) => r.date)
  const theme = dark ? DARK_LAYOUT : LIGHT_LAYOUT

  return (
    <Plot
      data={[
        {
          x: dates,
          y: data.map((r) => r.regime_code ?? null),
          type: 'scatter',
          mode: 'lines',
          fill: 'tozeroy',
          line: { color: '#3b82f6' },
          name: 'Regime',
        },
      ]}
      layout={{
        ...theme,
        title: { text: 'Regime History', font: { size: 14 } },
        yaxis: { ...theme.yaxis, tickvals: [1, 2, 3, 4], ticktext: ['Very Risk On', 'Risk On', 'Risk Off', 'Very Risk Off'] },
        margin: { t: 40, b: 40, l: 100, r: 20 },
        autosize: true,
      }}
      useResizeHandler
      style={{ width: '100%', height: 240 }}
      config={{ displayModeBar: false }}
    />
  )
}
