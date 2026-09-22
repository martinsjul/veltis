import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, PanelRightOpen } from 'lucide-react'
import FilterSidebar from './components/FilterSidebar'
import InstitutionPanel from './components/InstitutionPanel'
import MapView from './components/MapView'
import { getInstituicoes } from './services/institutionService'
import { matchesQuery } from './utils/institution'

const INITIAL_FILTERS = {
  query: '',
  municipio: '',
  tipos: [],
  redes: [],
}

export default function App() {
  const [institutions, setInstitutions] = useState([])
  const [selectedInstitution, setSelectedInstitution] = useState(null)
  const [filters, setFilters] = useState(INITIAL_FILTERS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function load() {
      try {
        setLoading(true)
        const data = await getInstituicoes()
        if (active) setInstitutions(data)
      } catch (err) {
        if (active) setError(err.message || 'Não foi possível carregar as instituições.')
      } finally {
        if (active) setLoading(false)
      }
    }

    load()

    return () => {
      active = false
    }
  }, [])

  const municipalities = useMemo(
    () => [...new Set(institutions.map((item) => item.municipio).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
    [institutions],
  )

  const filteredInstitutions = useMemo(() => {
    return institutions.filter((institution) => {
      const queryMatches = matchesQuery(institution, filters.query)
      const municipioMatches = !filters.municipio || institution.municipio === filters.municipio
      const tipoMatches = !filters.tipos.length || filters.tipos.includes(institution.tipo)
      const redeMatches = !filters.redes.length || filters.redes.includes(institution.rede)

      return queryMatches && municipioMatches && tipoMatches && redeMatches
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
        onReset={resetFilters}
      />

      <main className="map-area">
        <MapView
          institutions={filteredInstitutions}
          selectedInstitution={selectedInstitution}
          onSelect={setSelectedInstitution}
        />

        <div className="map-status">
          <span className="status-dot" />
          Região Metropolitana de Sorocaba
        </div>

        {loading && <div className="floating-message">Carregando instituições...</div>}

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
          Selecione um ponto no mapa para ver os detalhes
        </div>
      )}
    </div>
  )
}
