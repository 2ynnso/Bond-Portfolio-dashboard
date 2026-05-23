import React from 'react'
import Plot from 'react-plotly.js'
import type { NavRow } from '../../types'

interface Props {
  data: NavRow[]
  dark?: boolean
  title?: string
}

const DARK_LAYOUT = {
  paper_bgcolor: '#1f2937',
  plot_bgcolor: '#1f2937',
  font: { color: '#e5e7eb' },
  gridcolor: '#374151',
}

const LIGHT_LAYOUT = {
  paper_bgcolor: '#ffffff',
  plot_bgcolor: '#f9fafb',
  font: { color: '#111827' },
  gridcolor: '#e5e7eb',
}

export default function NavChart({ data, dark, title = 'TWR NAV vs AGG' }: Props) {
  const dates = data.map((r) => r.date)
  const theme = dark ? DARK_LAYOUT : LIGHT_LAYOUT

  return (
    <Plot
      data={[
        {
          x: dates,
          y: data.map((r) => r.Portfolio ?? null),
          name: 'Portfolio (TWR)',
          type: 'scatter',
          mode: 'lines',
          line: { color: '#3b82f6', width: 2 },
        },
        {
          x: dates,
          y: data.map((r) => r.AGG ?? null),
          name: 'AGG',
          type: 'scatter',
          mode: 'lines',
          line: { color: '#9ca3af', dash: 'dot' },
        },
      ]}
      layout={{
        ...theme,
        title: { text: title, font: { size: 14 } },
        xaxis: { gridcolor: theme.gridcolor },
        yaxis: { gridcolor: theme.gridcolor, title: 'NAV (base=100)' },
        legend: { x: 0, y: 1 },
        margin: { t: 40, b: 40, l: 60, r: 20 },
        autosize: true,
      }}
      useResizeHandler
      style={{ width: '100%', height: 360 }}
      config={{ displayModeBar: false }}
    />
  )
}
