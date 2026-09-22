import { X, MapPin, Building2, GraduationCap, CalendarDays, School } from 'lucide-react'

export default function InstitutionPanel({ institution, onClose }) {
  if (!institution) return null

  const isHigherEducation = institution.origem === 'MEC_IES'

  return (
    <aside className="detail-panel">
      <div className="detail-header">
        <div>
          <span className="eyebrow">Detalhes da instituição</span>
          <h2>{institution.nome}</h2>
          <div className="detail-badges">
            {institution.tipo && <span className="badge badge-type">{institution.tipo}</span>}
            {institution.rede && <span className="badge badge-network">{institution.rede}</span>}
          </div>
        </div>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Fechar detalhes">
          <X size={19} />
        </button>
      </div>

      <div className="detail-content">
        <section className="detail-section detail-intro">
          <div className="detail-icon"><School size={18} /></div>
          <div>
            <span className="detail-label">Identificação</span>
            <p>{institution.sigla || 'Sem sigla informada'}</p>
          </div>
        </section>

        <section className="detail-section">
          <div className="section-title">Localização</div>
          <InfoRow icon={<MapPin size={17} />} label="Município" value={`${institution.municipio} - ${institution.uf}`} />
          <InfoRow icon={<Building2 size={17} />} label="Endereço" value={formatAddress(institution)} />
        </section>

        <section className="detail-section">
          <div className="section-title">Base cadastral</div>
          <InfoRow icon={<CalendarDays size={17} />} label="Ano do censo" value={institution.anoCenso} />
          {institution.categoriaAdministrativa && (
            <InfoRow icon={<Building2 size={17} />} label="Categoria administrativa" value={institution.categoriaAdministrativa} />
          )}
          {institution.organizacaoAcademica && (
            <InfoRow icon={<GraduationCap size={17} />} label="Organização acadêmica" value={institution.organizacaoAcademica} />
          )}
          {institution.situacaoFuncionamento && (
            <InfoRow icon={<School size={17} />} label="Situação" value={institution.situacaoFuncionamento} />
          )}
        </section>

        {institution.possuiEnsinoMedio !== null && institution.possuiEnsinoMedio !== undefined && (
          <section className="detail-section">
            <div className="section-title">Ensino médio</div>
            <p className="detail-copy">
              {institution.possuiEnsinoMedio ? 'A instituição possui oferta de ensino médio conforme a base.' : 'Não consta oferta de ensino médio no campo informado.'}
            </p>
          </section>
        )}

        {isHigherEducation && (
          <section className="detail-section">
            <div className="section-title">Cursos</div>
            {institution.cursos?.length ? (
              <div className="course-list">
                {institution.cursos.map((curso) => (
                  <article className="course-card" key={curso.id}>
                    <h3>{curso.nome}</h3>
                    <div className="course-meta">
                      <span>{curso.grau || 'Grau não informado'}</span>
                      <span>{curso.modalidade || 'Modalidade não informada'}</span>
                    </div>
                    <div className="course-bottom">
                      <span>{curso.gratuito ? 'Gratuito' : 'Pago / não gratuito'}</span>
                      <span>{curso.vagas ?? '—'} vagas</span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-state">Nenhum curso associado foi retornado pelo back.</p>
            )}
          </section>
        )}
      </div>
    </aside>
  )
}

function InfoRow({ icon, label, value }) {
  return (
    <div className="info-row">
      <div className="info-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value || 'Não informado'}</strong>
      </div>
    </div>
  )
}

function formatAddress(institution) {
  return [institution.endereco, institution.bairro, institution.cep]
    .filter(Boolean)
    .join(' · ') || 'Endereço não informado'
}
