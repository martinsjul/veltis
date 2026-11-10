import { Search, SlidersHorizontal, RotateCcw, MapPinned } from 'lucide-react'

export default function FilterSidebar({
  filters,
  onChange,
  municipalities,
  resultCount,
  totalCount,
  hasScope = false,
  loadingInstitutions = false,
  onReset,
}) {
  return (
    <aside className="sidebar sidebar-left">
      <div className="brand-block">
        <div>
          <div className="brand-name">Veltis</div>
          <div className="brand-subtitle">Mapeamento educacional</div>
        </div>
      </div>

      <div className="sidebar-scroll">
        <section className="search-section">
          <label className="section-label" htmlFor="institution-search">
            Pesquisar instituição
          </label>
          <div className="search-box">
            <Search size={18} strokeWidth={2} />
            <input
              id="institution-search"
              value={filters.query}
              onChange={(event) => onChange({ query: event.target.value })}
              placeholder="Nome, sigla ou cidade..."
            />
          </div>
          <div className="result-counter">
            <MapPinned size={14} />
            {!hasScope ? (
              <span>Escolha um município ou pesquise pelo nome para ver as instituições.</span>
            ) : loadingInstitutions ? (
              <span>Buscando instituições...</span>
            ) : (
              <span>
                <strong>{resultCount}</strong>
                {resultCount !== totalCount ? ` de ${totalCount}` : ''} instituições no mapa
              </span>
            )}
          </div>
        </section>

        <section className="filter-section">
          <div className="filter-heading">
            <SlidersHorizontal size={17} />
            <span>Filtros</span>
          </div>

          <FilterField label="Município">
            <select
              value={filters.municipio}
              onChange={(event) => onChange({ municipio: event.target.value })}
            >
              <option value="">-</option>
              {municipalities.map((municipio) => (
                <option key={municipio} value={municipio}>
                  {municipio}
                </option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Nível de ensino">
            <div className="chip-grid">
              {[
                ['Escola', 'Educação básica'],
                ['Ensino superior', 'Ensino superior'],
              ].map(([value, label]) => {
                const active = filters.niveis.includes(value)
                return (
                  <button
                    type="button"
                    key={value}
                    className={`filter-chip ${active ? 'active' : ''}`}
                    onClick={() => {
                      const niveis = active
                        ? filters.niveis.filter((item) => item !== value)
                        : [...filters.niveis, value]
                      onChange({ niveis })
                    }}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </FilterField>

          <FilterField label="Rede">
            <div className="chip-grid">
              {['Pública', 'Estadual', 'Municipal', 'Federal', 'Privada'].map((value) => {
                const active = filters.redes.includes(value)
                return (
                  <button
                    type="button"
                    key={value}
                    className={`filter-chip ${active ? 'active' : ''}`}
                    onClick={() => {
                      const redes = active
                        ? filters.redes.filter((item) => item !== value)
                        : [...filters.redes, value]
                      onChange({ redes })
                    }}
                  >
                    {value}
                  </button>
                )
              })}
            </div>
          </FilterField>
        </section>
      </div>

      <button type="button" className="reset-button" onClick={onReset}>
        <RotateCcw size={16} />
        Limpar filtros
      </button>
    </aside>
  )
}

function FilterField({ label, children }) {
  return (
    <div className="filter-field">
      <label>{label}</label>
      {children}
    </div>
  )
}
