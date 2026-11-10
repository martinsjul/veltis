import { instituicoesMock } from './mockData'
import { normalizarTexto } from '../utils/institution'

// A API do Veltis publica as rotas na raiz (ex.: /municipios, /mapa/instituicoes),
// portanto VITE_API_URL deve ser http://127.0.0.1:8000, sem /api no final.
const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

const ROW_KEYS = [
  'dados', 'items', 'itens', 'results', 'resultados', 'registros',
  'instituicoes', 'municipios', 'municípios', 'data', 'features',
]

function readValue(record, ...aliases) {
  if (!record || typeof record !== 'object') return undefined
  const entries = Object.entries(record)
  for (const alias of aliases) {
    const match = entries.find(([key]) => key.toLowerCase() === String(alias).toLowerCase())
    if (match) return match[1]
  }
  return undefined
}

function rawRecord(value) {
  if (value?.type === 'Feature' && value.properties) {
    return { ...value.properties, geometry: value.geometry, _featureId: value.id }
  }
  return value && typeof value === 'object' ? value : {}
}

function extractRows(payload) {
  if (Array.isArray(payload)) return payload
  if (!payload || typeof payload !== 'object') return []
  if (payload.type === 'FeatureCollection' && Array.isArray(payload.features)) return payload.features
  for (const key of ROW_KEYS) {
    const value = readValue(payload, key)
    if (Array.isArray(value)) return value
  }
  // Algumas respostas envolvem o resultado em { data: { items: [...] } }.
  for (const key of ['data', 'resultado', 'result', 'response']) {
    const value = readValue(payload, key)
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const nested = extractRows(value)
      if (nested.length) return nested
    }
  }
  return []
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === '') return null
  const parsed = typeof value === 'number' ? value : Number(String(value).replace(',', '.'))
  return Number.isFinite(parsed) ? parsed : null
}

function stringOrNull(value) {
  if (value === null || value === undefined) return null
  const text = String(value).trim()
  return text || null
}

function codeKey(value) {
  return value === null || value === undefined ? '' : String(value).trim()
}

function normalizeMunicipalPayload(payload) {
  const rows = extractRows(payload)
  const codeToName = new Map()
  const optionsByCode = new Map()

  for (const value of rows) {
    const row = rawRecord(value)
    const code = codeKey(readValue(row, 'CD_MUN', 'cd_mun', 'codigo_ibge', 'codigo_municipio', 'co_municipio', 'id'))
    const name = stringOrNull(readValue(row, 'NM_MUN', 'nm_mun', 'nome_municipio', 'municipio', 'nome', 'name'))
    const uf = stringOrNull(readValue(row, 'SIGLA_UF', 'sg_uf', 'uf', 'sigla_uf')) || 'SP'
    if (code && name) codeToName.set(code, name)
    if (name) optionsByCode.set(code || name, { codigo: code, nome: name, uf })
  }

  let geoJson = null
  if (payload?.type === 'FeatureCollection' && Array.isArray(payload.features)) {
    geoJson = payload
  } else {
    const features = rows
      .map((value) => {
        if (value?.type === 'Feature' && value.geometry) return value
        const row = rawRecord(value)
        let geometry = readValue(row, 'geometry', 'geometria', 'geom', 'geojson', 'geo_json')
        if (typeof geometry === 'string') {
          try { geometry = JSON.parse(geometry) } catch { geometry = null }
        }
        if (!geometry || typeof geometry !== 'object' || !geometry.type || !Array.isArray(geometry.coordinates)) return null
        return { type: 'Feature', geometry, properties: { ...row } }
      })
      .filter(Boolean)
    if (features.length) geoJson = { type: 'FeatureCollection', features }
  }

  // Se os contornos vierem como features, também são a fonte dos nomes da lista.
  if (!optionsByCode.size && geoJson?.features) {
    for (const feature of geoJson.features) {
      const props = feature.properties || {}
      const code = codeKey(readValue(props, 'CD_MUN', 'cd_mun', 'codigo_ibge', 'codigo_municipio', 'id'))
      const name = stringOrNull(readValue(props, 'NM_MUN', 'nm_mun', 'nome_municipio', 'municipio', 'nome', 'name'))
      const uf = stringOrNull(readValue(props, 'SIGLA_UF', 'sg_uf', 'uf', 'sigla_uf')) || 'SP'
      if (code && name) codeToName.set(code, name)
      if (name) optionsByCode.set(code || name, { codigo: code, nome: name, uf })
    }
  }

  const options = [...optionsByCode.values()].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
  return { options, codeToName, geoJson }
}

async function apiGet(path, params = {}, { signal } = {}) {
  const url = new URL(`${API_URL}/${path.replace(/^\/+/, '')}`)
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value))
  }

  const response = await fetch(url, { signal })
  const text = await response.text()
  let payload
  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    payload = text
  }

  if (!response.ok) {
    const detail = payload && typeof payload === 'object'
      ? readValue(payload, 'detail', 'message', 'mensagem', 'error')
      : null
    const error = new Error(`${path}: HTTP ${response.status}${detail ? ` — ${typeof detail === 'string' ? detail : JSON.stringify(detail)}` : ''}`)
    error.status = response.status
    throw error
  }
  return payload
}

// ---------------------------------------------------------------- /mapa/instituicoes

function normalizeMapCourse(course, institution) {
  const isHigher = institution.origem === 'MEC_IES'
  const base = {
    id: `${institution.id}-curso-${course.codigo ?? course.nome}`,
    tipo: isHigher ? 'superior' : 'tecnico',
    nome: course.nome || (isHigher ? 'Curso superior não identificado' : 'Curso técnico não identificado'),
    anoRegistro: institution.anoCenso,
    municipio: institution.municipio,
    uf: institution.uf,
    codigoCurso: course.codigo ?? null,
    matriculas: numberOrNull(course.matriculas),
  }
  if (isHigher) {
    return {
      ...base,
      grau: stringOrNull(course.grau),
      areaGeral: stringOrNull(course.area),
      gratuito: typeof course.gratuito === 'boolean' ? course.gratuito : null,
      vagas: numberOrNull(course.vagas),
      modalidade: 'Presencial', // a API só lista oferta presencial no mapa
    }
  }
  return { ...base, areaProfissional: stringOrNull(course.area) }
}

// Converte um item de GET /mapa/instituicoes no formato usado pelo site.
function normalizeMapItem(item) {
  const isHigher = item.origem === 'MEC_IES'
  const institution = {
    id: String(item.id),
    codigoInep: item.codigoInep ?? null,
    codigoIES: item.codigoIes ?? null,
    codigoMunicipio: codeKey(item.codigoMunicipio),
    origem: item.origem,
    categoria: isHigher ? 'Ensino superior' : 'Escola',
    tipo: item.tipo,
    nome: item.nome,
    sigla: stringOrNull(item.sigla),
    nomeInstituicao: stringOrNull(item.nomeInstituicao),
    municipio: stringOrNull(item.municipio),
    uf: item.uf || 'SP',
    rede: stringOrNull(item.rede),
    categoriaAdministrativa: stringOrNull(item.categoriaAdministrativa),
    endereco: stringOrNull(item.endereco),
    bairro: stringOrNull(item.bairro),
    cep: stringOrNull(item.cep),
    telefone: stringOrNull(item.telefone),
    latitude: numberOrNull(item.latitude),
    longitude: numberOrNull(item.longitude),
    precisaoLocalizacao: stringOrNull(item.precisaoLocalizacao),
    anoCenso: numberOrNull(item.anoCenso),
    situacaoFuncionamento: stringOrNull(item.situacaoFuncionamento),
    possuiEnsinoMedio: isHigher ? null : boolOrNull(item.possuiEnsinoMedio),
    organizacaoAcademica: stringOrNull(item.organizacaoAcademica),
  }
  institution.cursos = (Array.isArray(item.cursos) ? item.cursos : []).map((c) => normalizeMapCourse(c, institution))
  return institution
}

function boolOrNull(value) {
  if (value === true || value === false) return value
  return null
}

// Cache simples por consulta: voltar a um município já visto não refaz a chamada.
const mapCache = new Map()

/**
 * Busca as instituições (com latitude/longitude e cursos) de UM município e/ou de uma busca por nome.
 * Nunca chame sem filtro: a lista completa é pesada e é justamente o que o mapa evita ao abrir.
 */
export async function getMapInstitutions({ municipioCodigo = '', municipioNome = '', busca = '', signal } = {}) {
  if (USE_MOCK) {
    const wantedCity = normalizarTexto(municipioNome)
    const wantedQuery = normalizarTexto(busca)
    return instituicoesMock.filter((item) => {
      if (wantedCity && normalizarTexto(item.municipio || '') !== wantedCity) return false
      if (wantedQuery && !normalizarTexto(`${item.nome} ${item.sigla || ''}`).includes(wantedQuery)) return false
      return true
    })
  }

  const params = {}
  if (municipioCodigo) params.municipio = municipioCodigo
  if (busca) params.busca = busca
  const cacheKey = JSON.stringify(params)
  if (mapCache.has(cacheKey)) return mapCache.get(cacheKey)

  const payload = await apiGet('/mapa/instituicoes', params, { signal })
  const items = extractRows(payload).map(normalizeMapItem)
  mapCache.set(cacheKey, items)
  return items
}

// ---------------------------------------------------------------- carga inicial (leve)

/** Só a lista de municípios (e seus contornos). As instituições são buscadas depois, sob demanda. */
export async function getCatalogData() {
  if (USE_MOCK) {
    const municipalities = [...new Set(instituicoesMock.map((item) => item.municipio).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, 'pt-BR'))
      .map((nome) => ({ nome, codigo: '', uf: 'SP' }))
    return { municipalities, municipalitiesGeoJson: null }
  }

  const municipalitiesData = normalizeMunicipalPayload(await apiGet('/municipios'))
  return {
    municipalities: municipalitiesData.options,
    municipalitiesGeoJson: municipalitiesData.geoJson,
  }
}
