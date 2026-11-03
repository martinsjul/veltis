# Diagrama de classes — Veltis

Modelo de domínio: as classes representam os conceitos que o portal apresenta e como se relacionam. Os atributos usam os nomes das colunas do banco (ver `docs/dados/`). Os métodos são as consultas que a API oferece para cada conceito.

Este diagrama substitui o do documento Veltis_1_1, que trazia atributos inexistentes na base (IDH, faixas de 15 a 64 e 65+ anos, turno do curso) e uma única classe para escola e faculdade.

```mermaid
classDiagram
    direction LR

    class Municipio {
        +cd_mun: str
        +nm_mun: str
        +area_km2: float
        +geometria: MultiPolygon
        +indicadores() IndicadoresMunicipio
        +resumo_educacao() ResumoEducacao
    }

    class IndicadorDemografico {
        +cd_agregado: str
        +cd_variavel: str
        +co_periodo: str
        +ds_chave_classificacao: str
        +js_classificacoes: list
        +vl_indicador: float
        +ds_unidade: str
    }

    class Escola {
        +co_entidade: int
        +no_entidade: str
        +nu_ano_censo: int
        +tp_dependencia: int
        +tp_localizacao: int
        +tp_situacao_funcionamento: int
        +oferece_ensino_medio: bool
        +e_etec() bool
        +melhor_localizacao() LocalizacaoEscola
    }

    class LocalizacaoEscola {
        +ds_endereco: str
        +nu_cep: str
        +nu_telefone: str
        +latitude: float
        +longitude: float
        +tp_metodo_localizacao: str
        +ds_precisao: str
        +vl_desvio_metros: int
    }

    class CursoTecnico {
        +co_curso_educ_profissional: int
        +no_curso_educ_profissional: str
        +no_area_curso_profissional: str
        +qt_mat_curso_tec: int
    }

    class InstituicaoSuperior {
        +co_ies: int
        +no_ies: str
        +sg_ies: str
        +tp_rede: int
        +tp_organizacao_academica: int
        +municipio_sede: str
        +e_fatec() bool
    }

    class LocalOferta {
        +no_local: str
        +ds_endereco: str
        +latitude: float
        +longitude: float
        +ds_precisao: str
    }

    class OfertaCursoSuperior {
        +co_curso: int
        +no_curso: str
        +tp_dimensao: int
        +tp_grau_academico: int
        +tp_modalidade_ensino: int
        +in_gratuito: bool
        +qt_vg_total: int
        +qt_mat: int
        +e_presencial() bool
    }

    class FonteDados {
        +no_orgao: str
        +no_fonte: str
        +ds_tipo_fonte: str
    }

    class CargaDados {
        +ds_versao: str
        +no_arquivo_origem: str
        +ds_hash_sha256: str
        +ds_status: str
        +qt_registros_carregados: int
    }

    Municipio "1" -- "0..*" IndicadorDemografico : possui
    Municipio "1" -- "0..*" Escola : localiza
    Escola "1" -- "0..*" LocalizacaoEscola : tem (uma por fonte)
    Escola "1" -- "0..*" CursoTecnico : oferta
    Municipio "1" -- "0..*" OfertaCursoSuperior : local de oferta
    InstituicaoSuperior "1" -- "0..*" OfertaCursoSuperior : oferta
    InstituicaoSuperior "1" -- "0..*" LocalOferta : tem campus
    Municipio "1" -- "0..*" LocalOferta : localiza
    FonteDados "1" -- "0..*" CargaDados : registra
    FonteDados "1" -- "0..*" LocalizacaoEscola : origina
```

**Fonte:** Elaborado pelos autores.

Observações:

- `Escola` e `InstituicaoSuperior` são classes diferentes porque vêm de censos diferentes e têm dados diferentes. No mapa, a API une as duas numa lista (`/mapa/instituicoes`), com o campo `tipo` (Escola, ETEC, FATEC, Faculdade/Universidade).
- `IndicadorDemografico` guarda um valor por linha; a classificação (sexo, faixa de idade...) faz parte do valor (DEC-003). Indicadores disponíveis: população 2022 e estimativas, área e densidade, sexo e faixas de idade, alfabetização, frequência escolar e nível de instrução. **Não há IDH** na base.
- `LocalOferta` existe porque o Censo da Educação Superior não publica coordenadas (DEC-001).
