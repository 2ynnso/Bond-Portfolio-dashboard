import { useQuery } from '@tanstack/react-query'
import { fetchMacro } from '../api/macro'
import type { MacroParams } from '../types'

export function useMacroData(params: MacroParams = {}) {
  return useQuery({
    queryKey: ['macro', params],
    queryFn: () => fetchMacro(params),
    staleTime: 30 * 60 * 1000, // 30 min
    retry: 2,
  })
}
