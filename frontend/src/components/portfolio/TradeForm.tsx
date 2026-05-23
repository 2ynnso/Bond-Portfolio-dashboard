import React, { useState } from 'react'
import { useAppendTrade } from '../../hooks/usePortfolio'

interface Props {
  dark?: boolean
}

const today = new Date().toISOString().slice(0, 10)

export default function TradeForm({ dark }: Props) {
  const [date, setDate] = useState(today)
  const [ticker, setTicker] = useState('')
  const [action, setAction] = useState<'BUY' | 'SELL'>('BUY')
  const [quantity, setQuantity] = useState('')
  const [priceUsd, setPriceUsd] = useState('')
  const [fxRate, setFxRate] = useState('1350')
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  const { mutate, isPending } = useAppendTrade()

  const bg = dark ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-800'
  const inputCls = `w-full rounded border px-2 py-1 text-sm ${dark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-300'}`

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setMsg(null)
    if (!ticker || !quantity || !priceUsd) {
      setMsg({ type: 'err', text: '티커, 수량, 매수가를 모두 입력하세요.' })
      return
    }
    mutate(
      {
        date,
        ticker: ticker.toUpperCase(),
        action,
        quantity: parseFloat(quantity),
        price_usd: parseFloat(priceUsd),
        fx_rate_krw: parseFloat(fxRate),
      },
      {
        onSuccess: (res) => {
          if (res.success) {
            setMsg({ type: 'ok', text: '거래가 저장되었습니다.' })
            setTicker('')
            setQuantity('')
            setPriceUsd('')
          } else {
            setMsg({ type: 'err', text: res.message ?? '저장 실패' })
          }
        },
        onError: (err) => setMsg({ type: 'err', text: String(err) }),
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className={`rounded-xl p-4 shadow ${bg} border ${dark ? 'border-gray-700' : 'border-gray-200'} flex flex-col gap-3`}>
      <h3 className="font-bold">거래 입력</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div>
          <label className="text-xs block mb-1">거래일</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="text-xs block mb-1">티커</label>
          <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="SHYG" className={inputCls} />
        </div>
        <div>
          <label className="text-xs block mb-1">거래 유형</label>
          <select value={action} onChange={(e) => setAction(e.target.value as 'BUY' | 'SELL')} className={inputCls}>
            <option>BUY</option>
            <option>SELL</option>
          </select>
        </div>
        <div>
          <label className="text-xs block mb-1">수량</label>
          <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="0" step="0.0001" min="0" className={inputCls} />
        </div>
        <div>
          <label className="text-xs block mb-1">매수가 USD</label>
          <input type="number" value={priceUsd} onChange={(e) => setPriceUsd(e.target.value)} placeholder="0.00" step="0.01" min="0" className={inputCls} />
        </div>
        <div>
          <label className="text-xs block mb-1">USD/KRW 환율</label>
          <input type="number" value={fxRate} onChange={(e) => setFxRate(e.target.value)} placeholder="1350" step="1" min="0" className={inputCls} />
        </div>
      </div>
      {msg && (
        <p className={`text-sm ${msg.type === 'ok' ? 'text-green-500' : 'text-red-500'}`}>{msg.text}</p>
      )}
      <button
        type="submit"
        disabled={isPending}
        className="self-start px-4 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium disabled:opacity-50"
      >
        {isPending ? '저장 중...' : '저장'}
      </button>
    </form>
  )
}
