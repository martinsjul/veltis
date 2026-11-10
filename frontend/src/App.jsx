import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, PanelRightOpen } from 'lucide-react'
import FilterSidebar from './components/FilterSidebar'
import InstitutionPanel from './components/InstitutionPanel'
import MapView from './components/MapView'
import { getCatalogData, getMapInstitutions } from './services/institutionService'
import { matchesQuery, normalizarTexto } from './utils/institution'

const MIN_SEARCH_LENGTH = 2
const SEARCH_DEBOUNCE_MS = 350

const INITIAL_FILTERS = {
  query: '',
  municipio: '',
  niveis: [],
  redes: [],
}

export default function App() {
  const [institutions, setInstitutions] = useState([])
  const [municipalityOptions, setMunicipalityOptions] = useState([])
  const [municipalitiesGeoJson, setMunicipalitiesGeoJson] = useState(null)
  const [selectedInstitution, setSelectedInstitution] = useState(null)
  const [filters, setFilters] = useState(INITIAL_FILTERS)
  const [loading, setLoading] = useState(true)
  const [loadingInstitutions, setLoadingInstitutions] = useState(false)
  const [error, setError] = useState('')
  const [institutionsError, setInstitutionsError] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  useEffect(() => {
    let active = true

    async function load() {
      try {
        setLoading(true)
        const catalog = await getCatalogData()
        if (active) {
          setInstitutions(catalog.institutions || [])
          setMunicipalityOptions(catalog.municipalities || [])
          setMunicipalitiesGeoJson(catalog.municipalitiesGeoJson || null)
        }
      } catch (err) {
        if (active) setError(err.message || 'Não foi possível carregar a lista de municípios.')
      } finally {
        if (active) setLoading(false)
      }
    }

    load()

    return () => {
      active = false
    }
  }, [])

  // Espera o usuário parar de digitar antes de consultar a API.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(filters.query.trim()), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [filters.query])

  const municipalities = useMemo(
    () => municipalityOptions.map((item) => (typeof item === 'string' ? item : item.nome)).filter(Boolean),
    [municipalityOptions],
  )

  // O que será buscado na API: um município (escolhido no filtro, ou digitado por inteiro na busca)
  // ou, sem município, uma busca por nome. Sem nenhum dos dois, nada é carregado.
  const scope = useMemo(() => {
    const wantedName = filters.municipio || debouncedQuery
    const match = wantedName
      ? municipalityOptions.find((item) => normalizarTexto(item.nome || '') === normalizarTexto(wantedName))
      : null
    if (match) return { municipioCodigo: match.codigo || '', municipioNome: match.nome, busca: '' }
    if (filters.municipio) return { municipioCodigo: '', municipioNome: filters.municipio, busca: '' }
    if (debouncedQuery.length >= MIN_SEARCH_LENGTH) return { municipioCodigo: '', municipioNome: '', busca: debouncedQuery }
    return null
  }, [filters.municipio, debouncedQuery, municipalityOptions])

  const scopeKey = scope ? `${scope.municipioCodigo}|${scope.municipioNome}|${scope.busca}` : ''

  useEffect(() => {
    if (!scope) {
      setInstitutions([])
      setLoadingInstitutions(false)
      setInstitutionsError('')
      return undefined
    }

    const controller = new AbortController()
    setLoadingInstitutions(true)
    setInstitutionsError('')
    getMapInstitutions({ ...scope, signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) setInstitutions(items)
      })
      .catch((err) => {
        if (controller.signal.aborted || err.name === 'AbortError') return
        setInstitutions([])
        setInstitutionsError(err.message || 'Não foi possível carregar as instituições.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingInstitutions(false)
      })

    return () => controller.abort()
    // scopeKey representa o conteúdo de `scope`.
  }, [scopeKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const filteredInstitutions = useMemo(() => {
    return institutions.filter((institution) => {
      const queryMatches = matchesQuery(institution, filters.query)
      const municipioMatches = !filters.municipio || normalizarTexto(institution.municipio || '') === normalizarTexto(filters.municipio)
      const nivelMatches = !filters.niveis.length || filters.niveis.includes(institution.categoria)
      const redeMatches = !filters.redes.length || filters.redes.includes(institution.rede)

      return queryMatches && municipioMatches && nivelMatches && redeMatches
    })
  }, [institutions, filters])

  function updateFilters(patch) {
    setFilters((current) => ({ ...current, ...patch }))
    setSelectedInstitution(null)
  }

  function resetFilters() {
    setFilters(INITIAL_FILTERS)
    setSelectedInstitution(null)
  }

  return (
    <div className="app-shell">
      <FilterSidebar
        filters={filters}
        onChange={updateFilters}
        municipalities={municipalities}
        resultCount={filteredInstitutions.length}
        totalCount={institutions.length}
        hasScope={Boolean(scope)}
        loadingInstitutions={loadingInstitutions}
        onReset={resetFilters}
      />

      <main className="map-area">
        <MapView
          institutions={filteredInstitutions}
          municipalitiesGeoJson={municipalitiesGeoJson}
          selectedMunicipality={filters.municipio}
          selectedInstitution={selectedInstitution}
          onSelect={setSelectedInstitution}
        />

        <div className="map-status">
          <span className="status-dot" />
          Região Metropolitana de Sorocaba
        </div>

        {loading && <div className="floating-message">Carregando mapa...</div>}

        {!loading && !error && loadingInstitutions && (
          <div className="floating-message">Buscando instituições...</div>
        )}

        {!loading && !error && institutionsError && (
          <div className="floating-message error-message">
            <AlertTriangle size={17} />
            {institutionsError}
          </div>
        )}

        {error && (
          <div className="floating-message error-message">
            <AlertTriangle size={17} />
            {error}
          </div>
        )}

      </main>

      {selectedInstitution && (
        <>
          <button
            type="button"
            className="mobile-detail-backdrop"
            onClick={() => setSelectedInstitution(null)}
            aria-label="Fechar detalhes"
          />
          <InstitutionPanel
            institution={selectedInstitution}
            onClose={() => setSelectedInstitution(null)}
          />
        </>
      )}

      {!selectedInstitution && (
        <div className="map-tip">
          <PanelRightOpen size={16} />
          Escolha um município (ou pesquise) e selecione um ponto para ver os detalhes
        </div>
      )}
    </div>
  )
}
