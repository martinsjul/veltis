export const TIPO_LABELS = {
  Escola: 'Escola',
  ETEC: 'ETEC',
  FATEC: 'FATEC',
  'Faculdade/Universidade': 'Ensino superior',
}

export const TIPO_COLORS = {
  Escola: '#2A6F97',
  ETEC: '#0E7490',
  FATEC: '#D97706',
  'Faculdade/Universidade': '#7C3AED',
}

export function getMarkerColor(tipo) {
  return TIPO_COLORS[tipo] ?? '#315B62'
}

export function normalizarTexto(value = '') {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

export function matchesQuery(instituicao, query) {
  if (!query.trim()) return true

  const q = normalizarTexto(query)
  return [
    instituicao.nome,
    instituicao.sigla,
    instituicao.municipio,
    instituicao.tipo,
    instituicao.rede,
  ]
    .filter(Boolean)
    .some((value) => normalizarTexto(value).includes(q))
}
