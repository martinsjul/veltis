"""Pipelines 6 e 7 - INEP Censo da Educação Superior -> MEC_IES e MEC_CURSOS.

Regras (ver relatório "Fontes de dados do Veltis"):
  - TP_DIMENSAO: 1 presencial; 2 EAD por município; 3 EAD só nível Brasil;
    4 EAD no exterior. Só 1 e 2 têm município, então só elas entram.
  - O município do curso é o LOCAL DE OFERTA. A sede da IES pode estar
    fora da RMS (ex.: UNIP, IFSP, UFSCar), por isso as IES carregadas são
    as que OFERTAM na RMS, identificadas a partir do arquivo de cursos.
  - Na dimensão 2, QT_CURSO, vagas e inscritos vêm zerados pelo INEP;
    matrículas, ingressantes e concluintes vêm preenchidos.

IES e cursos são gravados na mesma transação: o ano é substituído
inteiro, o que também remove ofertas que deixaram de existir.

Executar sozinho:  python -m src.collectors.censo_superior [--forcar]
"""

import argparse
import re
import zipfile
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.collectors.download import baixar_arquivo
from src.config.edicoes import (
    ANO_CENSO_SUPERIOR,
    URL_CENSO_SUPERIOR,
    URL_PAGINA_CENSO_SUPERIOR,
)
from src.config.rms import CODIGOS_RMS
from src.loaders.carga import para_registros, upsert
from src.loaders.ingestao import Fonte, carga, hash_arquivo
from src.transforms import codigos as conv
from src.validators import basicos as validar


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw" / "inep" / "censo_superior"

FONTE = Fonte(
    orgao="INEP",
    nome="Censo da Educação Superior",
    url_oficial=URL_PAGINA_CENSO_SUPERIOR,
    periodicidade="Anual",
    observacao="IES e cursos de graduação por local de oferta.",
)

DIMENSOES_COM_MUNICIPIO = ["1", "2"]

COLUNAS_CURSOS = [
    "NU_ANO_CENSO", "TP_DIMENSAO", "CO_IES", "CO_CURSO", "NO_CURSO",
    "CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF", "NO_CINE_AREA_GERAL",
    "NO_CINE_AREA_ESPECIFICA", "TP_GRAU_ACADEMICO", "IN_GRATUITO",
    "TP_MODALIDADE_ENSINO", "TP_NIVEL_ACADEMICO", "QT_CURSO",
    "QT_VG_TOTAL", "QT_MAT",
]

COLUNAS_IES = [
    "NU_ANO_CENSO", "CO_IES", "NO_IES", "SG_IES", "CO_MUNICIPIO_IES",
    "NO_MUNICIPIO_IES", "SG_UF_IES", "TP_ORGANIZACAO_ACADEMICA", "TP_REDE",
    "TP_CATEGORIA_ADMINISTRATIVA", "DS_ENDERECO_IES", "DS_NUMERO_ENDERECO_IES",
    "DS_COMPLEMENTO_ENDERECO_IES", "NO_BAIRRO_IES", "NU_CEP_IES",
]


# ============================================================
# PACOTE OFICIAL
# ============================================================

def obter_pacote(forcar: bool = False) -> Path:
    destino = DATA_DIR / f"microdados_censo_da_educacao_superior_{ANO_CENSO_SUPERIOR}.zip"
    return baixar_arquivo(URL_CENSO_SUPERIOR, destino, forcar=forcar)


def localizar_csv(caminho_zip: Path, trecho: str) -> str:
    """Busca tolerante: o INEP já publicou nomes diferentes no mesmo pacote."""

    with zipfile.ZipFile(caminho_zip) as pacote:
        candidatos = [
            nome for nome in pacote.namelist()
            if re.search(rf"{trecho}.*\.csv$", nome, re.IGNORECASE)
        ]

    if len(candidatos) != 1:
        raise RuntimeError(
            f"Esperávamos exatamente um CSV com '{trecho}', encontramos: {candidatos}"
        )

    return candidatos[0]


def ler_csv(caminho_zip: Path, nome_csv: str, colunas: list[str]) -> pd.DataFrame:
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
# TRANSFORMAÇÃO
# ============================================================

def processar_cursos(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    origem = "Cursos (Censo Superior)"

    df = df[df["TP_DIMENSAO"].isin(DIMENSOES_COM_MUNICIPIO)].copy()
    df["CO_MUNICIPIO"] = conv.codigo_municipio(df["CO_MUNICIPIO"])
    df = df[df["CO_MUNICIPIO"].isin(CODIGOS_RMS)].copy()
    validar.nao_vazio(df, origem)

    saida = pd.DataFrame(
        {
            "nu_ano_censo": conv.para_inteiro(df["NU_ANO_CENSO"]),
            "tp_dimensao": conv.para_inteiro(df["TP_DIMENSAO"]),
            "co_ies": conv.para_inteiro(df["CO_IES"]),
            "co_curso": conv.para_inteiro(df["CO_CURSO"]),
            "no_curso": conv.para_texto(df["NO_CURSO"], 255),
            "co_municipio": df["CO_MUNICIPIO"],
            "no_municipio": conv.para_texto(df["NO_MUNICIPIO"], 150),
            "sg_uf": conv.para_texto(df["SG_UF"], 2),
            "no_cine_area_geral": conv.para_texto(df["NO_CINE_AREA_GERAL"], 120),
            "no_cine_area_especifica": conv.para_texto(df["NO_CINE_AREA_ESPECIFICA"], 120),
            "tp_grau_academico": conv.para_inteiro(df["TP_GRAU_ACADEMICO"]),
            "in_gratuito": conv.para_booleano(df["IN_GRATUITO"]),
            "tp_modalidade_ensino": conv.para_inteiro(df["TP_MODALIDADE_ENSINO"]),
            "tp_nivel_academico": conv.para_inteiro(df["TP_NIVEL_ACADEMICO"]),
            "qt_curso": conv.para_inteiro(df["QT_CURSO"]),
            "qt_vg_total": conv.para_inteiro(df["QT_VG_TOTAL"]),
            "qt_mat": conv.para_inteiro(df["QT_MAT"]),
        }
    )

    chave = ["nu_ano_censo", "co_curso", "tp_dimensao", "co_municipio"]
    validar.sem_duplicidade(saida, chave, origem)
    validar.sem_nulos(
        saida,
        ["nu_ano_censo", "tp_dimensao", "co_ies", "co_curso", "no_curso",
         "co_municipio", "in_gratuito", "tp_modalidade_ensino",
         "tp_nivel_academico", "qt_curso", "qt_vg_total", "qt_mat"],
        origem,
    )
    validar.dominio(saida["nu_ano_censo"], [ano], origem)
    validar.dominio(saida["tp_dimensao"], [1, 2], origem)
    validar.dominio(saida["tp_modalidade_ensino"], [1, 2], origem)
    validar.dominio(saida["tp_nivel_academico"], [1, 2], origem)
    validar.dominio(saida["tp_grau_academico"], [1, 2, 3, 4], origem, permitir_nulo=True)

    if (saida[["qt_curso", "qt_vg_total", "qt_mat"]] < 0).any().any():
        raise validar.ErroValidacao(f"{origem}: quantidades negativas.")

    presenciais = saida[saida["tp_dimensao"] == 1]
    print(
        f"Ofertas na RMS: {len(saida)} "
        f"({len(presenciais)} presenciais em {presenciais['co_municipio'].nunique()} "
        f"municípios; {len(saida) - len(presenciais)} EAD por município)."
    )
    return saida


def montar_endereco(df: pd.DataFrame) -> pd.Series:
    """'Rua X, 123 - Bloco A' a partir das três colunas de endereço."""

    def limpo(valor) -> str:
        texto = str(valor).strip()
        return "" if texto in {"-", "--", "."} else texto

    def juntar(linha):
        logradouro = limpo(linha["DS_ENDERECO_IES"])
        numero = limpo(linha["DS_NUMERO_ENDERECO_IES"])
        complemento = limpo(linha["DS_COMPLEMENTO_ENDERECO_IES"])

        if not logradouro:
            return None

        texto = f"{logradouro}, {numero}" if numero else logradouro
        if complemento:
            texto = f"{texto} - {complemento}"

        return texto[:255]

    return conv.como_objeto((juntar(linha) for _, linha in df.iterrows()), df.index)


def processar_ies(df: pd.DataFrame, ano: int, ies_com_oferta: set[int]) -> pd.DataFrame:
    origem = "IES (Censo Superior)"

    df = df.copy()
    df["_co_ies"] = conv.para_inteiro(df["CO_IES"])
    df = df[df["_co_ies"].isin(ies_com_oferta)].copy()

    saida = pd.DataFrame(
        {
            "nu_ano_censo": conv.para_inteiro(df["NU_ANO_CENSO"]),
            "co_ies": df["_co_ies"],
            "no_ies": conv.para_texto(df["NO_IES"], 255),
            "sg_ies": conv.para_texto(df["SG_IES"], 50),
            "co_municipio_ies": conv.codigo_municipio(df["CO_MUNICIPIO_IES"]),
            "no_municipio_ies": conv.para_texto(df["NO_MUNICIPIO_IES"], 150),
            "sg_uf_ies": conv.para_texto(df["SG_UF_IES"], 2),
            "tp_organizacao_academica": conv.para_inteiro(df["TP_ORGANIZACAO_ACADEMICA"]),
            "tp_rede": conv.para_inteiro(df["TP_REDE"]),
            "tp_categoria_administrativa": conv.para_inteiro(df["TP_CATEGORIA_ADMINISTRATIVA"]),
            "ds_endereco_ies": montar_endereco(df),
            "no_bairro_ies": conv.para_texto(df["NO_BAIRRO_IES"], 100),
            "nu_cep_ies": conv.como_objeto(
                (conv.somente_digitos(v, 8) for v in df["NU_CEP_IES"]), df.index
            ),
        }
    )

    faltando = sorted(ies_com_oferta - set(saida["co_ies"]))
    if faltando:
        raise validar.ErroValidacao(
            f"{origem}: {len(faltando)} IES com oferta na RMS não estão no arquivo de IES: "
            f"{faltando[:10]}"
        )

    validar.sem_duplicidade(saida, ["nu_ano_censo", "co_ies"], origem)
    validar.sem_nulos(
        saida,
        ["nu_ano_censo", "co_ies", "no_ies", "co_municipio_ies", "no_municipio_ies",
         "sg_uf_ies", "tp_organizacao_academica", "tp_rede",
         "tp_categoria_administrativa"],
        origem,
    )
    validar.dominio(saida["nu_ano_censo"], [ano], origem)
    validar.dominio(saida["tp_organizacao_academica"], [1, 2, 3, 4, 5], origem)
    validar.dominio(saida["tp_rede"], [1, 2], origem)
    validar.dominio(saida["tp_categoria_administrativa"], range(1, 10), origem)

    sede_fora = int((~saida["co_municipio_ies"].isin(CODIGOS_RMS)).sum())
    print(f"IES com oferta na RMS: {len(saida)} ({sede_fora} com sede fora da RMS).")
    return saida


# ============================================================
# CARGA
# ============================================================

def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== INEP - CENSO DA EDUCAÇÃO SUPERIOR ===")

    caminho_zip = obter_pacote(forcar=forcar)
    hash_ = hash_arquivo(caminho_zip)

    with carga(
        FONTE,
        periodo=str(ANO_CENSO_SUPERIOR),
        versao=f"Censo da Educação Superior {ANO_CENSO_SUPERIOR}",
        arquivo=caminho_zip.name,
        hash_arquivo=hash_,
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        df_cursos = ler_csv(caminho_zip, localizar_csv(caminho_zip, "CADASTRO_CURSOS"), COLUNAS_CURSOS)
        cursos = processar_cursos(df_cursos, ANO_CENSO_SUPERIOR)

        df_ies = ler_csv(caminho_zip, localizar_csv(caminho_zip, "_IES_"), COLUNAS_IES)
        ies = processar_ies(df_ies, ANO_CENSO_SUPERIOR, set(cursos["co_ies"]))

        cursos["id_ingestao"] = ing.id_ingestao
        ies["id_ingestao"] = ing.id_ingestao

        # Substitui o ano inteiro (cursos antes das IES por causa da FK).
        ing.conexao.execute(
            text("DELETE FROM mec_cursos WHERE nu_ano_censo = :ano"),
            {"ano": ANO_CENSO_SUPERIOR},
        )
        ing.conexao.execute(
            text("DELETE FROM mec_ies WHERE nu_ano_censo = :ano"),
            {"ano": ANO_CENSO_SUPERIOR},
        )

        upsert(ing.conexao, "mec_ies", para_registros(ies), chave=["nu_ano_censo", "co_ies"])
        carregados = upsert(
            ing.conexao,
            "mec_cursos",
            para_registros(cursos),
            chave=["nu_ano_censo", "co_curso", "tp_dimensao", "co_municipio"],
        )

        ing.registrar_contagens(
            lidos=len(df_cursos),
            carregados=carregados,
            observacao=(
                f"{carregados} ofertas (dimensões 1 e 2) e {len(ies)} IES "
                "com oferta na RMS."
            ),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true")
    executar_pipeline(forcar=parser.parse_args().forcar)
