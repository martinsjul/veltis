import {
  X,
  MapPin,
  Building2,
  GraduationCap,
  CalendarDays,
  School,
  BookOpen,
  Database,
  Users,
} from 'lucide-react'

export default function InstitutionPanel({ institution, onClose }) {
  if (!institution) return null

  return (
    <aside className="detail-panel">
      <div className="detail-header">
        <div>
          <span className="eyebrow">Detalhes da instituição</span>
          <h2>{institution.nome}</h2>
          <div className="detail-badges">
            {institution.tipo && <span className="badge badge-type">{institution.tipo}</span>}
            {institution.rede && <span className="badge badge-network">{institution.rede}</span>}
            {institution.categoria && <span className="badge badge-level">{institution.categoria}</span>}
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
          {institution.precisaoLocalizacao && (
            <InfoRow icon={<MapPin size={17} />} label="Precisão do ponto no mapa" value={precisionLabel(institution.precisaoLocalizacao)} />
          )}
        </section>

        <section className="detail-section">
          <div className="section-title">Base cadastral</div>
          <InfoRow icon={<Database size={17} />} label="Fonte" value={sourceLabel(institution.origem)} />
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
              {institution.possuiEnsinoMedio
                ? 'A instituição possui oferta de ensino médio conforme o registro da base.'
                : 'Não consta oferta de ensino médio no campo informado.'}
            </p>
          </section>
        )}

        {institution.cursos?.length > 0 && (
          <section className="detail-section">
            <div className="section-title">Cursos e ofertas</div>
            <div className="course-list">
              {institution.cursos.map((curso) => (
                <CourseCard curso={curso} key={curso.id} />
              ))}
            </div>
          </section>
        )}
      </div>
    </aside>
  )
}

function CourseCard({ curso }) {
  const isTechnical = curso.tipo === 'tecnico'
  const courseSource = isTechnical ? 'INEP — Censo Escolar' : 'MEC — Censo da Educação Superior'

  return (
    <article className="course-card">
      <div className="course-card-header">
        <div>
          <span className="course-source">{courseSource}</span>
          <h3>{curso.nome}</h3>
        </div>
        <span className="course-year">{curso.anoRegistro || '—'}</span>
      </div>

      <div className="course-origin-row">
        <span><CalendarDays size={13} /> Registro de {curso.anoRegistro || '—'}</span>
        {curso.municipio && <span>{curso.municipio} · {curso.uf || 'SP'}</span>}
      </div>

      {isTechnical ? (
        <>
          <div className="course-data-grid">
            <CourseData label="Área profissional" value={curso.areaProfissional} />
            <CourseData label="ID do curso técnico" value={curso.codigoCurso} />
            <CourseData label="ID da área profissional" value={curso.codigoAreaProfissional} />
            <CourseData label="Quantidade de cursos" value={curso.quantidadeCursoTecnico} />
            <CourseData icon={<Users size={13} />} label="Matrículas técnicas" value={curso.matriculas} />
          </div>
        </>
      ) : (
        <>
          <div className="course-data-grid">
            <CourseData label="Grau acadêmico" value={curso.grau} />
            <CourseData label="Modalidade" value={curso.modalidade} />
            <CourseData label="Nível acadêmico" value={curso.nivel} />
            <CourseData label="Área geral CINE" value={curso.areaGeral} />
            <CourseData label="Área específica CINE" value={curso.areaEspecifica} />
            <CourseData label="Gratuito" value={formatBoolean(curso.gratuito)} />
            <CourseData label="Dimensão do registro" value={curso.dimensao} />
            <CourseData label="ID da oferta" value={curso.idOferta} />
            <CourseData label="ID do curso" value={curso.codigoCurso} />
            <CourseData label="Quantidade no registro" value={curso.quantidadeCurso} />
            <CourseData icon={<GraduationCap size={13} />} label="Vagas totais" value={curso.vagas} />
            <CourseData icon={<Users size={13} />} label="Matrículas" value={curso.matriculas} />
          </div>
        </>
      )}

      <div className="course-footer">
        <BookOpen size={13} />
        <span>{isTechnical ? 'Registro de curso técnico' : 'Registro de curso superior'}</span>
      </div>
    </article>
  )
}

function CourseData({ icon, label, value }) {
  return (
    <div className="course-data">
      <span>{icon}{label}</span>
      <strong>{value === null || value === undefined || value === '' ? 'Não informado' : value}</strong>
    </div>
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

function sourceLabel(origem) {
  if (origem === 'INEP_ESCOLA') return 'INEP — Censo Escolar'
  if (origem === 'MEC_IES') return 'MEC — Censo da Educação Superior'
  return origem || 'Base não informada'
}

function precisionLabel(precisao) {
  return ({
    edificio: 'No prédio',
    numero: 'No número do endereço',
    rua: 'Na rua certa (pode estar a algumas quadras)',
    oficial: 'Coordenada oficial (INEP/SEDUC)',
    numero_aproximado: 'Número aproximado (geocodificado)',
    logradouro: 'No logradouro (geocodificado)',
  })[precisao] || precisao
}

function formatBoolean(value) {
  if (value === true) return 'Sim'
  if (value === false) return 'Não'
  return 'Não informado'
}
