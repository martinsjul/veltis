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

// O texto pesquisável de cada instituição é normalizado uma única vez (e não a cada tecla digitada).
const searchTextCache = new WeakMap()

function searchableText(instituicao) {
  let text = searchTextCache.get(instituicao)
  if (text === undefined) {
    text = normalizarTexto(
      [
        instituicao.nome,
        instituicao.sigla,
        instituicao.nomeInstituicao,
        instituicao.municipio,
        instituicao.tipo,
        instituicao.rede,
      ]
        .filter(Boolean)
        .join(' '),
    )
    searchTextCache.set(instituicao, text)
  }
  return text
}

export function matchesQuery(instituicao, query) {
  if (!query.trim()) return true
  return searchableText(instituicao).includes(normalizarTexto(query))
}
