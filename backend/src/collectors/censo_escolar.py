"""Pipelines 3 e 4 - INEP Censo Escolar -> INEP_ESCOLA e INEP_CURSO_TECNICO.

Os dois usam o MESMO pacote oficial (~537 MB), baixado uma vez:
    Tabela_Escola_<ano>_V2.csv         -> INEP_ESCOLA
    Tabela_Curso_Tecnico_<ano>_V2.csv  -> INEP_CURSO_TECNICO

Executar sozinho:  python -m src.collectors.censo_escolar [--forcar]
"""

import argparse
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

from src.collectors.download import CABECALHOS, baixar_arquivo
from src.config.edicoes import (
    ANO_CENSO_ESCOLAR,
    URL_CENSO_ESCOLAR,
    URL_PAGINA_CENSO_ESCOLAR,
)
from src.config.rms import CODIGOS_RMS
from src.loaders.carga import para_registros, upsert
from src.loaders.ingestao import Fonte, carga, hash_arquivo
from src.transforms import codigos as conv
from src.validators import basicos as validar


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw" / "inep" / "censo_escolar"

FONTE = Fonte(
    orgao="INEP",
    nome="Censo Escolar",
    url_oficial=URL_PAGINA_CENSO_ESCOLAR,
    periodicidade="Anual",
    observacao="Fonte mestre das escolas de educação básica do Veltis.",
)

COLUNAS_ESCOLA = [
    "NU_ANO_CENSO", "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO",
    "NO_MUNICIPIO", "SG_UF", "TP_DEPENDENCIA", "TP_LOCALIZACAO",
    "TP_SITUACAO_FUNCIONAMENTO", "IN_COMUM_MEDIO_MEDIO",
    "IN_COMUM_MEDIO_INTEGRADO", "IN_COMUM_MEDIO_FIC",
    "IN_COMUM_MEDIO_NORMAL", "IN_ITINERARIO_TECN_PROF",
]

INDICADORES_ESCOLA = [c for c in COLUNAS_ESCOLA if c.startswith("IN_")]

COLUNAS_CURSO = [
    "NU_ANO_CENSO", "CO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO",
    "CO_CURSO_EDUC_PROFISSIONAL", "NO_CURSO_EDUC_PROFISSIONAL",
    "ID_AREA_CURSO_PROFISSIONAL", "NO_AREA_CURSO_PROFISSIONAL",
    "QT_CURSO_TEC", "QT_MAT_CURSO_TEC",
]


# ============================================================
# PACOTE OFICIAL
# ============================================================

def descobrir_url(ano: int) -> str:
    """Procura na página do INEP o link do ano configurado.

    Se a página mudar ou estiver fora do ar, usa a URL fixa da config.
    """

    try:
        resposta = requests.get(URL_PAGINA_CENSO_ESCOLAR, headers=CABECALHOS, timeout=60)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")

        for link in soup.find_all("a", href=True):
            texto = link.get_text(" ", strip=True)
            href = link["href"]

            if (
                "Microdados do Censo Escolar" in texto
                and re.search(rf"\b{ano}\b", texto)
                and "download.inep.gov.br" in href
            ):
                return href

        print(f"Link de {ano} não encontrado na página; usando a URL configurada.")
    except requests.RequestException as erro:
        print(f"Página do INEP indisponível ({erro}); usando a URL configurada.")

    return URL_CENSO_ESCOLAR


def obter_pacote(forcar: bool = False) -> Path:
    url = descobrir_url(ANO_CENSO_ESCOLAR)
    destino = DATA_DIR / f"microdados_censo_escolar_{ANO_CENSO_ESCOLAR}.zip"
    return baixar_arquivo(url, destino, forcar=forcar)


def localizar_csv(caminho_zip: Path, prefixo: str) -> str:
    with zipfile.ZipFile(caminho_zip) as pacote:
        candidatos = [
            nome for nome in pacote.namelist()
            if re.search(rf"{prefixo}_.*\.csv$", nome, re.IGNORECASE)
        ]

    if len(candidatos) != 1:
        raise RuntimeError(
            f"Esperávamos exatamente um arquivo {prefixo} no pacote, "
            f"mas encontramos {len(candidatos)}: {candidatos}"
        )

    return candidatos[0]


def ler_csv(caminho_zip: Path, nome_csv: str, colunas: list[str]) -> pd.DataFrame:
    """Lê só as colunas usadas, tudo como texto (latin-1, separador ;)."""

    with zipfile.ZipFile(caminho_zip) as pacote:
        with pacote.open(nome_csv) as arquivo:
            cabecalho = arquivo.readline().decode("latin-1").strip().split(";")

        validar.colunas_presentes(pd.DataFrame(columns=cabecalho), colunas, nome_csv)

        with pacote.open(nome_csv) as arquivo:
            df = pd.read_csv(
                arquivo,
                sep=";",
                encoding="latin-1",
                usecols=colunas,
                dtype=str,
                keep_default_na=False,
            )

    print(f"{Path(nome_csv).name}: {len(df)} registros nacionais lidos.")
    return df


# ============================================================
# ESCOLAS
# ============================================================

def processar_escolas(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    origem = "Tabela_Escola"

    validar.colunas_presentes(df, COLUNAS_ESCOLA, origem)
    df = df[COLUNAS_ESCOLA].copy()

    df["CO_MUNICIPIO"] = conv.codigo_municipio(df["CO_MUNICIPIO"])
    df = df[df["CO_MUNICIPIO"].isin(CODIGOS_RMS)].copy()
    validar.nao_vazio(df, origem)

    saida = pd.DataFrame(
        {
            "nu_ano_censo": conv.para_inteiro(df["NU_ANO_CENSO"]),
            "co_entidade": conv.para_inteiro(df["CO_ENTIDADE"]),
            "no_entidade": conv.para_texto(df["NO_ENTIDADE"], 255),
            "co_municipio": df["CO_MUNICIPIO"],
            "no_municipio": conv.para_texto(df["NO_MUNICIPIO"], 150),
            "sg_uf": conv.para_texto(df["SG_UF"], 2),
            "tp_dependencia": conv.para_inteiro(df["TP_DEPENDENCIA"]),
            "tp_localizacao": conv.para_inteiro(df["TP_LOCALIZACAO"]),
            "tp_situacao_funcionamento": conv.para_inteiro(df["TP_SITUACAO_FUNCIONAMENTO"]),
        }
    )

    # Indicadores 0/1. Vazio = "não se aplica" (escola paralisada ou extinta).
    for coluna in INDICADORES_ESCOLA:
        saida[coluna.lower()] = conv.para_booleano(df[coluna])

    validar.apenas_rms(saida["co_municipio"], origem)
    validar.sem_duplicidade(saida, ["nu_ano_censo", "co_entidade"], origem)
    validar.sem_nulos(
        saida,
        ["nu_ano_censo", "co_entidade", "no_entidade", "co_municipio",
         "no_municipio", "sg_uf", "tp_dependencia", "tp_localizacao",
         "tp_situacao_funcionamento"],
        origem,
    )
    validar.dominio(saida["nu_ano_censo"], [ano], origem)
    validar.dominio(saida["tp_dependencia"], [1, 2, 3, 4], origem)
    validar.dominio(saida["tp_localizacao"], [1, 2], origem)
    validar.dominio(saida["tp_situacao_funcionamento"], [1, 2, 3, 4], origem)

    print(f"Escolas na RMS: {len(saida)}")
    return saida


def carregar_escolas(caminho_zip: Path, hash_: str, forcar: bool) -> None:
    nome_csv = localizar_csv(caminho_zip, "Tabela_Escola")

    with carga(
        FONTE,
        periodo=str(ANO_CENSO_ESCOLAR),
        versao=f"Censo Escolar {ANO_CENSO_ESCOLAR} ({Path(nome_csv).stem})",
        arquivo=Path(nome_csv).name,
        hash_arquivo=hash_,
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        df = ler_csv(caminho_zip, nome_csv, COLUNAS_ESCOLA)
        escolas = processar_escolas(df, ANO_CENSO_ESCOLAR)
        escolas["id_ingestao"] = ing.id_ingestao

        carregados = upsert(
            ing.conexao,
            "inep_escola",
            para_registros(escolas),
            chave=["nu_ano_censo", "co_entidade"],
        )

        ativas = int((escolas["tp_situacao_funcionamento"] == 1).sum())
        ing.registrar_contagens(
            lidos=len(df),
            carregados=carregados,
            observacao=f"Tabela de escolas filtrada para a RMS; {ativas} em atividade.",
        )


# ============================================================
# CURSOS TÉCNICOS
# ============================================================

def processar_cursos_tecnicos(
    df: pd.DataFrame,
    ano: int,
    escolas_no_banco: set[int],
) -> pd.DataFrame:
    origem = "Tabela_Curso_Tecnico"

    validar.colunas_presentes(df, COLUNAS_CURSO, origem)
    df = df[COLUNAS_CURSO].copy()

    df["CO_MUNICIPIO"] = conv.codigo_municipio(df["CO_MUNICIPIO"])
    df = df[df["CO_MUNICIPIO"].isin(CODIGOS_RMS)].copy()
    validar.nao_vazio(df, origem)

    saida = pd.DataFrame(
        {
            "nu_ano_censo": conv.para_inteiro(df["NU_ANO_CENSO"]),
            "co_entidade": conv.para_inteiro(df["CO_ENTIDADE"]),
            "co_municipio": df["CO_MUNICIPIO"],
            "no_municipio": conv.para_texto(df["NO_MUNICIPIO"], 150),
            "co_curso_educ_profissional": conv.para_inteiro(df["CO_CURSO_EDUC_PROFISSIONAL"]),
            "no_curso_educ_profissional": conv.para_texto(df["NO_CURSO_EDUC_PROFISSIONAL"], 255),
            "id_area_curso_profissional": conv.para_inteiro(df["ID_AREA_CURSO_PROFISSIONAL"]),
            "no_area_curso_profissional": conv.para_texto(df["NO_AREA_CURSO_PROFISSIONAL"], 255),
            "qt_curso_tec": conv.para_inteiro(df["QT_CURSO_TEC"]),
            "qt_mat_curso_tec": conv.para_inteiro(df["QT_MAT_CURSO_TEC"]),
        }
    )

    validar.sem_duplicidade(
        saida, ["nu_ano_censo", "co_entidade", "co_curso_educ_profissional"], origem
    )
    validar.sem_nulos(
        saida,
        ["nu_ano_censo", "co_entidade", "co_municipio", "no_municipio",
         "co_curso_educ_profissional", "no_curso_educ_profissional"],
        origem,
    )
    validar.dominio(saida["nu_ano_censo"], [ano], origem)

    sem_escola = sorted(set(saida["co_entidade"]) - escolas_no_banco)
    if sem_escola:
        raise validar.ErroValidacao(
            f"{origem}: {len(sem_escola)} escolas dos cursos não estão em INEP_ESCOLA "
            f"(rode antes a carga de escolas). Exemplos: {sem_escola[:5]}"
        )

    if (saida[["qt_curso_tec", "qt_mat_curso_tec"]].dropna() < 0).any().any():
        raise validar.ErroValidacao(f"{origem}: quantidades negativas.")

    print(
        f"Cursos técnicos na RMS: {len(saida)} linhas, "
        f"{saida['co_entidade'].nunique()} escolas, "
        f"{int(saida['qt_mat_curso_tec'].sum())} matrículas."
    )
    return saida


def carregar_cursos_tecnicos(caminho_zip: Path, hash_: str, forcar: bool) -> None:
    nome_csv = localizar_csv(caminho_zip, "Tabela_Curso_Tecnico")

    with carga(
        FONTE,
        periodo=str(ANO_CENSO_ESCOLAR),
        versao=f"Censo Escolar {ANO_CENSO_ESCOLAR} ({Path(nome_csv).stem})",
        arquivo=Path(nome_csv).name,
        hash_arquivo=hash_,
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        escolas_no_banco = set(
            ing.conexao.execute(
                text("SELECT co_entidade FROM inep_escola WHERE nu_ano_censo = :ano"),
                {"ano": ANO_CENSO_ESCOLAR},
            ).scalars()
        )

        df = ler_csv(caminho_zip, nome_csv, COLUNAS_CURSO)
        cursos = processar_cursos_tecnicos(df, ANO_CENSO_ESCOLAR, escolas_no_banco)
        cursos["id_ingestao"] = ing.id_ingestao

        carregados = upsert(
            ing.conexao,
            "inep_curso_tecnico",
            para_registros(cursos),
            chave=["nu_ano_censo", "co_entidade", "co_curso_educ_profissional"],
        )

        ing.registrar_contagens(
            lidos=len(df),
            carregados=carregados,
            observacao=(
                "Cursos de educação profissional das escolas da RMS. "
                "Área 999 = Normal/Magistério."
            ),
        )


# ============================================================
# PIPELINE
# ============================================================

def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== INEP - CENSO ESCOLAR ===")

    caminho_zip = obter_pacote(forcar=forcar)
    hash_ = hash_arquivo(caminho_zip)

    carregar_escolas(caminho_zip, hash_, forcar)
    carregar_cursos_tecnicos(caminho_zip, hash_, forcar)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true")
    executar_pipeline(forcar=parser.parse_args().forcar)
