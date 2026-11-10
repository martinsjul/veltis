"""Formato das respostas da API.

Estes modelos aparecem na documentação automática (/docs), então o
frontend sabe exatamente quais campos vêm em cada endereço.
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    total: int = Field(description="Total de itens que atendem aos filtros.")
    pagina: int
    por_pagina: int
    itens: list[T]


# ---------------------------------------------------------------- municípios

class IndicadoresMunicipio(BaseModel):
    cd_mun: str
    nm_mun: str
    populacao_2022: int | None = None
    taxa_crescimento_2010_2022_pct: float | None = Field(None, description="Crescimento médio anual, em %.")
    populacao_estimada_2026: int | None = None
    area_km2: float | None = None
    densidade_hab_km2: float | None = None
    homens: int | None = None
    mulheres: int | None = None
    populacao_0_14: int | None = None
    populacao_15_29: int | None = None
    populacao_60_mais: int | None = None
    pessoas_15_mais: int | None = None
    alfabetizados_15_mais: int | None = None
    frequencia_escolar_0_3_pct: float | None = None
    frequencia_escolar_4_5_pct: float | None = None
    frequencia_escolar_6_14_pct: float | None = None
    frequencia_escolar_15_17_pct: float | None = None
    frequencia_escolar_18_24_pct: float | None = None
    pessoas_18_mais: int | None = None
    superior_completo_18_mais: int | None = None


class ResumoEducacao(BaseModel):
    ano_censo_escolar: int | None
    escolas_ativas: int
    escolas_ativas_ensino_medio: int
    escolas_ativas_educacao_profissional: int
    cursos_tecnicos: int = Field(description="Cursos técnicos ofertados (sem Normal/Magistério).")
    matriculas_cursos_tecnicos: int
    ano_censo_superior: int | None
    instituicoes_presenciais: int = Field(description="Instituições com curso presencial no município.")
    cursos_superiores_presenciais: int
    cursos_superiores_ead: int = Field(description="Cursos EAD com alunos morando no município.")


class FichaMunicipio(BaseModel):
    cd_mun: str
    nm_mun: str
    indicadores: IndicadoresMunicipio
    educacao: ResumoEducacao


# ------------------------------------------------------------------- escolas

class CursoTecnicoDaEscola(BaseModel):
    co_curso_educ_profissional: int
    no_curso_educ_profissional: str | None
    id_area_curso_profissional: int | None
    no_area_curso_profissional: str | None
    e_normal_magisterio: bool
    qt_mat_curso_tec: int | None


class EscolaDetalhe(BaseModel):
    nu_ano_censo: int
    co_entidade: int
    no_entidade: str
    co_municipio: str
    no_municipio: str | None
    ds_dependencia: str | None
    ds_localizacao: str | None
    ds_situacao: str | None
    em_atividade: bool
    oferece_ensino_medio: bool | None
    oferece_medio_integrado: bool | None
    oferece_normal_magisterio: bool | None
    oferece_itinerario_tecnico: bool | None
    qt_cursos_tecnicos: int
    qt_matriculas_educ_profissional: int
    ds_endereco: str | None
    nu_cep: str | None
    nu_telefone: str | None
    fonte_localizacao: str | None
    tp_metodo_localizacao: str | None
    tem_coordenada: bool
    ponto_confere_municipio: bool | None
    latitude: float | None
    longitude: float | None
    ds_precisao_localizacao: str | None = Field(
        description="oficial; ou numero, numero_aproximado, logradouro (geocodificado)."
    )
    vl_desvio_metros: int | None = Field(description="Margem de erro do ponto geocodificado.")
    cursos_tecnicos: list[CursoTecnicoDaEscola]


class EscolaSemLocalizacao(BaseModel):
    co_entidade: int
    no_entidade: str
    co_municipio: str
    no_municipio: str | None
    ds_dependencia: str | None
    ds_situacao: str | None
    ds_endereco: str | None = Field(description="Algumas têm endereço, mas não têm coordenada.")
    fonte_localizacao: str | None


# -------------------------------------------------------------------- cursos

class CursoTecnico(BaseModel):
    nu_ano_censo: int
    co_entidade: int
    no_entidade: str
    ds_dependencia: str | None
    co_municipio: str
    no_municipio: str | None
    co_curso_educ_profissional: int
    no_curso_educ_profissional: str | None
    id_area_curso_profissional: int | None
    no_area_curso_profissional: str | None
    e_normal_magisterio: bool
    qt_mat_curso_tec: int | None


class CursoSuperior(BaseModel):
    nu_ano_censo: int
    co_municipio: str
    no_municipio: str | None
    co_ies: int
    no_ies: str
    sg_ies: str | None
    ds_rede: str | None
    ds_organizacao_academica: str | None
    sede_no_municipio: bool
    co_curso: int
    no_curso: str
    no_cine_area_geral: str | None
    no_cine_area_especifica: str | None
    ds_grau_academico: str | None
    ds_modalidade: str | None
    e_presencial: bool
    e_gratuito: bool | None
    qt_vagas: int | None = Field(description="Só existe na oferta presencial.")
    qt_matriculas: int | None
    com_matricula: bool | None


class LocalDaInstituicao(BaseModel):
    no_local: str
    ds_endereco: str | None
    latitude: float
    longitude: float
    ds_precisao_localizacao: str


class InstituicaoNoMunicipio(BaseModel):
    co_ies: int
    no_ies: str
    sg_ies: str | None
    ds_rede: str | None
    ds_organizacao_academica: str | None
    co_municipio: str
    no_municipio: str | None
    sede_no_municipio: bool
    qt_cursos_presenciais: int
    qt_cursos_ead: int
    qt_matriculas: int
    locais: list[LocalDaInstituicao] = Field(
        description="Campi com coordenada no município (vazio se a faculdade só tem EAD ali)."
    )


# ---------------------------------------------------------------------- mapa

class CursoNoMapa(BaseModel):
    codigo: int
    nome: str | None
    grau: str | None = Field(None, description="Só nos cursos superiores.")
    area: str | None = None
    gratuito: bool | None = Field(None, description="Só nos cursos superiores.")
    vagas: int | None = Field(None, description="Só nos cursos superiores presenciais.")
    matriculas: int | None = None


class InstituicaoNoMapa(BaseModel):
    """Escola ou faculdade, no formato que o frontend usa no mapa."""

    id: str = Field(description="'escola-<código INEP>' ou 'ies-<co_ies>-<id do local>'.")
    origem: str = Field(description="INEP_ESCOLA ou MEC_IES.")
    tipo: str = Field(description="Escola, ETEC, FATEC ou Faculdade/Universidade.")
    nome: str
    sigla: str | None
    nomeInstituicao: str | None = Field(description="Nome oficial da faculdade (MEC_IES).")
    codigoInep: int | None = Field(description="Código INEP da escola.")
    codigoIes: int | None = Field(description="Código da faculdade no INEP.")
    municipio: str | None
    codigoMunicipio: str
    uf: str
    rede: str | None
    categoriaAdministrativa: str | None
    endereco: str | None
    bairro: str | None
    cep: str | None
    telefone: str | None
    latitude: float | None
    longitude: float | None
    precisaoLocalizacao: str | None = Field(
        description=(
            "Escolas: oficial (INEP/SEDUC) ou, se geocodificada pelo endereço, "
            "numero, numero_aproximado ou logradouro. Faculdades: edificio, numero ou rua."
        )
    )
    anoCenso: int
    situacaoFuncionamento: str | None
    possuiEnsinoMedio: bool | None
    organizacaoAcademica: str | None
    cursos: list[CursoNoMapa]


# ------------------------------------------------------------ filtros/fontes

class Opcao(BaseModel):
    valor: str
    rotulo: str


class OpcoesDeFiltro(BaseModel):
    municipios: list[Opcao]
    dependencias: list[Opcao]
    areas_tecnicas: list[Opcao]
    modalidades: list[Opcao]
    graus_academicos: list[Opcao]
    redes: list[Opcao]
    areas_cine: list[Opcao]


class Carga(BaseModel):
    no_orgao: str
    no_fonte: str
    no_arquivo_origem: str | None
    co_periodo_referencia: str | None
    ds_status: str
    dt_processamento: datetime | None
    qt_registros_lidos: int | None
    qt_registros_carregados: int | None
    qt_registros_rejeitados: int | None
    ds_observacao: str | None


class Saude(BaseModel):
    status: str
    banco: str
