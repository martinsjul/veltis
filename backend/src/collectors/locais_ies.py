"""Pipeline 7 - Locais de oferta das faculdades (coordenadas) -> IES_LOCAL_OFERTA.

O Censo da Educação Superior não traz coordenadas, só o endereço da
SEDE de cada instituição. Por isso o ponto de cada campus da RMS foi
levantado à mão e fica num arquivo versionado no repositório:

    backend/data/referencia/ies_locais_oferta.csv   (separador ;)

Cada linha = um campus: instituição (co_ies), município, endereço,
latitude/longitude, precisão do ponto e de onde veio cada informação.
Para corrigir um ponto, edite o CSV e rode esta etapa de novo.

Executar sozinho:  python -m src.collectors.locais_ies [--forcar]
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.loaders.carga import para_registros
from src.loaders.ingestao import Fonte, carga, hash_arquivo
from src.validators import basicos as validar


BASE_DIR = Path(__file__).resolve().parents[2]
ARQUIVO = BASE_DIR / "data" / "referencia" / "ies_locais_oferta.csv"

FONTE = Fonte(
    orgao="Veltis",
    nome="Locais de oferta das IES (levantamento)",
    url_oficial="https://github.com/martinsjul/veltis/blob/main/backend/data/referencia/ies_locais_oferta.csv",
    periodicidade="Sob demanda",
    tipo="INTERNA",
    observacao=(
        "Endereços: INEP (sede) e sites oficiais das instituições. "
        "Coordenadas: OpenStreetMap (ODbL), conferidas no polígono do município."
    ),
)

COLUNAS = [
    "co_ies", "cd_mun", "no_local", "ds_endereco", "no_bairro", "nu_cep",
    "latitude", "longitude", "ds_precisao", "ds_fonte_endereco",
    "ds_fonte_coordenada", "ds_observacao",
]
PRECISOES = {"edificio", "numero", "rua"}
ORIGEM = "Locais das IES"


def ler_locais(caminho: Path = ARQUIVO) -> pd.DataFrame:
    df = pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8", keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def processar_locais(df: pd.DataFrame) -> pd.DataFrame:
    """Valida o CSV e devolve as linhas no formato da tabela."""

    validar.colunas_presentes(df, COLUNAS, ORIGEM)
    validar.nao_vazio(df, ORIGEM)

    saida = df[COLUNAS].apply(lambda s: s.str.strip()).replace("", None)

    saida["co_ies"] = pd.to_numeric(saida["co_ies"], errors="raise").astype("int64")
    saida["nu_cep"] = saida["nu_cep"].str.replace(r"\D", "", regex=True).replace("", None)
    for coluna in ("latitude", "longitude"):
        saida[coluna] = pd.to_numeric(saida[coluna].str.replace(",", "."), errors="raise")

    validar.sem_nulos(
        saida,
        ["co_ies", "cd_mun", "no_local", "latitude", "longitude",
         "ds_precisao", "ds_fonte_endereco", "ds_fonte_coordenada"],
        ORIGEM,
    )
    validar.apenas_rms(saida["cd_mun"], ORIGEM)
    validar.dominio(saida["ds_precisao"], PRECISOES, ORIGEM)
    validar.sem_duplicidade(saida, ["co_ies", "cd_mun", "no_local"], ORIGEM)

    fora_de_sp = saida[
        ~saida["latitude"].between(-25.5, -19.5) | ~saida["longitude"].between(-53.5, -44.0)
    ]
    if not fora_de_sp.empty:
        raise validar.ErroValidacao(
            f"{ORIGEM}: coordenadas fora do estado de SP (latitude/longitude trocadas?): "
            f"{fora_de_sp['no_local'].tolist()}"
        )

    invalidos = saida[saida["nu_cep"].notna() & (saida["nu_cep"].str.len() != 8)]
    if not invalidos.empty:
        raise validar.ErroValidacao(
            f"{ORIGEM}: CEP com tamanho errado: {invalidos['no_local'].tolist()}"
        )

    saida = saida.rename(columns={"latitude": "vl_latitude", "longitude": "vl_longitude"})
    saida["geometry"] = saida.apply(
        lambda r: f"POINT({r['vl_longitude']} {r['vl_latitude']})", axis=1
    )
    return saida


def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== LOCAIS DAS FACULDADES (coordenadas dos campi) ===")

    if not ARQUIVO.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO}")

    with carga(
        FONTE,
        periodo="atual",
        versao="Levantamento de locais de oferta presencial",
        arquivo=ARQUIVO.name,
        hash_arquivo=hash_arquivo(ARQUIVO),
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        df = ler_locais()
        locais = processar_locais(df)

        ies_conhecidas = set(
            ing.conexao.execute(text("SELECT DISTINCT co_ies FROM mec_ies")).scalars()
        )
        if not ies_conhecidas:
            raise validar.ErroValidacao(
                "MEC_IES está vazia; rode antes o pipeline do Censo Superior."
            )
        desconhecidas = sorted(set(locais["co_ies"]) - ies_conhecidas)
        if desconhecidas:
            raise validar.ErroValidacao(
                f"{ORIGEM}: co_ies que não existem em MEC_IES: {desconhecidas}"
            )

        # O arquivo é a lista completa: substitui tudo o que havia.
        ing.conexao.execute(text("DELETE FROM ies_local_oferta"))

        registros = para_registros(locais.assign(id_ingestao=ing.id_ingestao))
        ing.conexao.execute(
            text(
                """
                INSERT INTO ies_local_oferta (
                    co_ies, cd_mun, no_local, ds_endereco, no_bairro, nu_cep,
                    vl_latitude, vl_longitude, geometry, ds_precisao,
                    ds_fonte_endereco, ds_fonte_coordenada, ds_observacao, id_ingestao
                ) VALUES (
                    :co_ies, :cd_mun, :no_local, :ds_endereco, :no_bairro, :nu_cep,
                    :vl_latitude, :vl_longitude, ST_GeomFromText(:geometry, 4674), :ds_precisao,
                    :ds_fonte_endereco, :ds_fonte_coordenada, :ds_observacao, :id_ingestao
                )
                """
            ),
            registros,
        )

        fora_do_municipio = ing.conexao.execute(
            text(
                """
                SELECT array_agg(l.no_local ORDER BY l.no_local)
                FROM ies_local_oferta l
                JOIN ibge_municipios m ON m.cd_mun = l.cd_mun
                WHERE NOT ST_Intersects(m.geometry, l.geometry)
                """
            )
        ).scalar_one()
        if fora_do_municipio:
            raise validar.ErroValidacao(
                f"{ORIGEM}: pontos fora do polígono do próprio município: {fora_do_municipio}"
            )

        sem_local = ing.conexao.execute(
            text("SELECT COUNT(*) FROM vw_faculdades_sem_local")
        ).scalar_one()

        resumo = locais["ds_precisao"].value_counts().to_dict()
        print(
            f"{len(locais)} locais gravados {resumo}; "
            f"{sem_local} ofertas presenciais ainda sem local."
        )

        ing.registrar_contagens(
            lidos=len(df),
            carregados=len(locais),
            observacao=f"Precisão: {resumo}. Ofertas presenciais sem local: {sem_local}.",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true")
    executar_pipeline(forcar=parser.parse_args().forcar)
