import { Search, SlidersHorizontal, RotateCcw, MapPinned } from 'lucide-react'
import { TIPO_LABELS } from '../utils/institution'

export default function FilterSidebar({
  filters,
  onChange,
  municipalities,
  resultCount,
  totalCount,
  onReset,
}) {
  return (
    <aside className="sidebar sidebar-left">
      <div className="brand-block">
        <div className="brand-mark">V</div>
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
            <span>
              <strong>{resultCount}</strong> de {totalCount} instituições no mapa
            </span>
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
              <option value="">Todos os municípios</option>
              {municipalities.map((municipio) => (
                <option key={municipio} value={municipio}>
                  {municipio}
                </option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Tipo de instituição">
            <div className="chip-grid">
              {Object.entries(TIPO_LABELS).map(([value, label]) => {
                const active = filters.tipos.includes(value)
                return (
                  <button
                    type="button"
                    key={value}
                    className={`filter-chip ${active ? 'active' : ''}`}
                    onClick={() => {
                      const tipos = active
                        ? filters.tipos.filter((item) => item !== value)
                        : [...filters.tipos, value]
                      onChange({ tipos })
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
