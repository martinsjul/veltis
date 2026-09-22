import { instituicoesMock } from './mockData'

const API_URL = import.meta.env.VITE_API_URL || ''
const USE_MOCK = !API_URL

export async function getInstituicoes() {
  if (USE_MOCK) return instituicoesMock

  const response = await fetch(`${API_URL}/instituicoes`)

  if (!response.ok) {
    throw new Error(`Erro ao carregar instituições: ${response.status}`)
  }

  const data = await response.json()
  return Array.isArray(data) ? data : data.instituicoes ?? []
}
