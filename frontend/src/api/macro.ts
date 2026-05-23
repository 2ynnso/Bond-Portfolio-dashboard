import type { MacroParams, MacroResponse } from '../types'
import api from './client'

export async function fetchMacro(params: MacroParams = {}): Promise<MacroResponse> {
  const { data } = await api.get<MacroResponse>('/macro', { params })
  return data
}
