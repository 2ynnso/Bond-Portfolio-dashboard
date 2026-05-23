import React from 'react'

interface SidebarParams {
  years: number
  oasWindow: number
  vixThresh: number
  oasZThresh: number
  pprLow: number
  pprHigh: number
  includePpr: boolean
  dark: boolean
  onChange: (key: string, value: number | boolean) => void
}

export default function Sidebar({ years, oasWindow, vixThresh, oasZThresh, pprLow, pprHigh, includePpr, dark, onChange }: SidebarParams) {
  const bg = dark ? 'bg-gray-900 text-gray-100' : 'bg-white text-gray-800'
  const border = dark ? 'border-gray-700' : 'border-gray-200'

  return (
    <aside className={`fixed top-0 left-0 h-full w-60 border-r ${bg} ${border} p-4 flex flex-col gap-4 z-10 overflow-y-auto`}>
      <div className="text-lg font-bold">Control</div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={dark}
          onChange={(e) => onChange('dark', e.target.checked)}
          className="w-4 h-4"
        />
        <span>Dark Mode</span>
      </label>

      <div>
        <label className="block text-sm mb-1">조회 기간: {years}년</label>
        <input
          type="range" min={1} max={15} value={years}
          onChange={(e) => onChange('years', +e.target.value)}
          className="w-full"
        />
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={includePpr}
          onChange={(e) => onChange('includePpr', e.target.checked)}
          className="w-4 h-4"
        />
        <span className="text-sm">PPR(SHYG) 포함</span>
      </label>

      <div>
        <p className="text-sm font-medium mb-1">OAS Z 롤링 윈도우</p>
        <div className="flex gap-2">
          {[12, 24, 36].map((w) => (
            <button
              key={w}
              onClick={() => onChange('oasWindow', w)}
              className={`flex-1 py-1 rounded text-sm border ${oasWindow === w ? 'bg-blue-500 text-white border-blue-500' : `${border} ${dark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}`}
            >
              {w}M
            </button>
          ))}
        </div>
      </div>

      <details className={`text-sm border rounded p-2 ${border}`}>
        <summary className="cursor-pointer font-medium">Regime 임계값 설정</summary>
        <div className="flex flex-col gap-3 mt-2">
          {[
            { label: `VIX 임계값: ${vixThresh.toFixed(0)}`, key: 'vixThresh', min: 15, max: 50, step: 1, val: vixThresh },
            { label: `OAS Z 임계값: ${oasZThresh.toFixed(1)}`, key: 'oasZThresh', min: -2, max: 2, step: 0.1, val: oasZThresh },
            { label: `PPR 저점: ${pprLow.toFixed(2)}`, key: 'pprLow', min: 0.05, max: 0.45, step: 0.05, val: pprLow },
            { label: `PPR 고점: ${pprHigh.toFixed(2)}`, key: 'pprHigh', min: 0.55, max: 0.95, step: 0.05, val: pprHigh },
          ].map(({ label, key, min, max, step, val }) => (
            <div key={key}>
              <label className="block mb-1">{label}</label>
              <input
                type="range" min={min} max={max} step={step} value={val}
                onChange={(e) => onChange(key, +e.target.value)}
                className="w-full"
              />
            </div>
          ))}
        </div>
      </details>
    </aside>
  )
}
