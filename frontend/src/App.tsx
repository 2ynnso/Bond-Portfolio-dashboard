import React, { useState } from 'react'
import Sidebar from './components/layout/Sidebar'
import SignalTab from './components/signal/SignalTab'
import PortfolioTab from './components/portfolio/PortfolioTab'
import type { MacroParams } from './types'

type Tab = 'signal' | 'portfolio'

export default function App() {
  const [tab, setTab] = useState<Tab>('signal')
  const [dark, setDark] = useState(false)
  const [params, setParams] = useState<MacroParams & { dark: boolean }>({
    years: 8,
    oasWindow: 24,
    vixThresh: 25,
    oasZThresh: 1.0,
    pprLow: 0.2,
    pprHigh: 0.8,
    includePpr: true,
    dark: false,
  })

  function handleSidebarChange(key: string, value: number | boolean) {
    if (key === 'dark') {
      setDark(value as boolean)
    }
    setParams((prev) => ({ ...prev, [key]: value }))
  }

  const macroParams: MacroParams = {
    years: params.years,
    oas_window: params.oasWindow as number,
    vix_thresh: params.vixThresh as number,
    oas_z_thresh: params.oasZThresh as number,
    ppr_low: params.pprLow as number,
    ppr_high: params.pprHigh as number,
    include_ppr: params.includePpr as boolean,
  }

  const base = dark ? 'bg-gray-950 text-gray-100 min-h-screen' : 'bg-gray-50 text-gray-900 min-h-screen'

  return (
    <div className={`${base} ${dark ? 'dark' : ''}`}>
      <Sidebar
        years={params.years as number}
        oasWindow={params.oasWindow as number}
        vixThresh={params.vixThresh as number}
        oasZThresh={params.oasZThresh as number}
        pprLow={params.pprLow as number}
        pprHigh={params.pprHigh as number}
        includePpr={params.includePpr as boolean}
        dark={dark}
        onChange={handleSidebarChange}
      />

      <main className="ml-60 p-6 flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Bond Signal Dashboard</h1>
          <p className="text-sm opacity-60">{new Date().toLocaleDateString('ko-KR')}</p>
        </div>

        {/* Tabs */}
        <div className={`flex gap-1 rounded-lg p-1 ${dark ? 'bg-gray-800' : 'bg-gray-200'} w-fit`}>
          {(['signal', 'portfolio'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === t
                  ? 'bg-blue-500 text-white shadow'
                  : `${dark ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`
              }`}
            >
              {t === 'signal' ? '📊 Signal Board' : '💰 Portfolio'}
            </button>
          ))}
        </div>

        {tab === 'signal' ? (
          <SignalTab params={macroParams} dark={dark} />
        ) : (
          <PortfolioTab dark={dark} />
        )}
      </main>
    </div>
  )
}
