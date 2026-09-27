import hashlib
import re
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

from src.config.rms import CODIGOS_RMS
from src.database import engine


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "raw" / "inep" / "censo_escolar"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PAGINA_OFICIAL = (
    "https://www.gov.br/inep/pt-br/"
    "acesso-a-informacao/dados-abertos/"
    "microdados/censo-escolar"
)


# ============================================================
# DESCOBRIR EDIÇÃO MAIS RECENTE
# ============================================================

def descobrir_edicao() -> tuple[int, str]:

    print("Consultando página oficial do Censo Escolar...")

    resposta = requests.get(
        PAGINA_OFICIAL,
        timeout=60,
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(
        resposta.text,
        "html.parser",
    )

    edicoes = []

    for link in soup.find_all("a", href=True):

        texto = link.get_text(
            " ",
            strip=True,
        )

        href = link["href"]

        if "Microdados do Censo Escolar" not in texto:
            continue

        match = re.search(
            r"\b(20\d{2})\b",
            texto,
        )

        if not match:
            continue

        ano = int(match.group(1))

        if "download.inep.gov.br" not in href:
            continue

        edicoes.append(
            (ano, href)
        )

    if not edicoes:
        raise RuntimeError(
            "Nenhum pacote do Censo Escolar "
            "foi encontrado na página oficial."
        )

    ano, url = max(
        edicoes,
        key=lambda item: item[0],
    )

    print(
        f"Edição mais recente encontrada: {ano}"
    )

    return ano, url


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_pacote(
    ano: int,
    url: str,
) -> Path:

    caminho = (
        DATA_DIR
        / f"microdados_censo_escolar_{ano}.zip"
    )

    caminho_tmp = caminho.with_suffix(".zip.tmp")

    print(
        f"Baixando Censo Escolar {ano}..."
    )

    sessao = requests.Session()

    sessao.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Referer": PAGINA_OFICIAL,
        }
    )

    tentativas = 3

    for tentativa in range(
        1,
        tentativas + 1,
    ):

        try:

            print(
                f"Tentativa {tentativa}/{tentativas}..."
            )

            resposta = sessao.get(
                url,
                stream=True,
                timeout=(30, 300),
            )

            resposta.raise_for_status()

            with caminho_tmp.open("wb") as arquivo:

                for bloco in resposta.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if bloco:
                        arquivo.write(bloco)

            caminho_tmp.replace(caminho)

            print("Download concluído.")

            return caminho

        except requests.RequestException as erro:

            print(
                f"Falha no download: {erro}"
            )

            caminho_tmp.unlink(
                missing_ok=True
            )

            if tentativa == tentativas:
                raise RuntimeError(
                    "O servidor do INEP não respondeu "
                    "após 3 tentativas."
                ) from erro


# ============================================================
# HASH
# ============================================================

def calcular_hash(
    caminho: Path,
) -> str:

    sha256 = hashlib.sha256()

    with caminho.open("rb") as arquivo:

        for bloco in iter(
            lambda: arquivo.read(
                1024 * 1024
            ),
            b"",
        ):
            sha256.update(bloco)

    return sha256.hexdigest()


# ============================================================
# LOCALIZAR TABELA DE ESCOLAS
# ============================================================

def localizar_csv_escolas(
    caminho_zip: Path,
) -> str:

    with zipfile.ZipFile(
        caminho_zip,
        "r",
    ) as pacote:

        candidatos = [
            nome
            for nome in pacote.namelist()
            if re.search(
                r"Tabela_Escola_.*\.csv$",
                nome,
                re.IGNORECASE,
            )
        ]

    if len(candidatos) != 1:
        raise RuntimeError(
            "Esperávamos exatamente uma "
            "Tabela_Escola no pacote, "
            f"mas encontramos {len(candidatos)}."
        )

    print(
        "Arquivo de escolas encontrado:"
    )
    print(candidatos[0])

    return candidatos[0]


# ============================================================
# LER CSV
# ============================================================

def ler_escolas(
    caminho_zip: Path,
    nome_csv: str,
) -> pd.DataFrame:

    print("Lendo tabela de escolas...")

    with zipfile.ZipFile(
        caminho_zip,
        "r",
    ) as pacote:

        with pacote.open(nome_csv) as arquivo:

            df = pd.read_csv(
                arquivo,
                sep=";",
                encoding="latin-1",
                low_memory=False,
            )

    print(
        f"Registros nacionais lidos: {len(df)}"
    )

    return df


# ============================================================
# TRANSFORMAR E VALIDAR
# ============================================================

def processar_escolas(
    df: pd.DataFrame,
    ano: int,
) -> pd.DataFrame:

    colunas = [
        "NU_ANO_CENSO",
        "CO_ENTIDADE",
        "NO_ENTIDADE",
        "CO_MUNICIPIO",
        "NO_MUNICIPIO",
        "SG_UF",
        "TP_DEPENDENCIA",
        "TP_LOCALIZACAO",
        "TP_SITUACAO_FUNCIONAMENTO",
        "IN_COMUM_MEDIO_MEDIO",
        "IN_COMUM_MEDIO_INTEGRADO",
        "IN_COMUM_MEDIO_FIC",
        "IN_COMUM_MEDIO_NORMAL",
        "IN_ITINERARIO_TECN_PROF",
    ]

    faltantes = [
        coluna
        for coluna in colunas
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "O arquivo mudou de estrutura. "
            "Colunas esperadas não encontradas: "
            f"{faltantes}"
        )

    df = df[colunas].copy()

    df["CO_MUNICIPIO"] = (
        df["CO_MUNICIPIO"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )

    df_rms = df[
        df["CO_MUNICIPIO"].isin(
            CODIGOS_RMS
        )
    ].copy()

    if df_rms.empty:
        raise ValueError(
            "Nenhuma escola da RMS foi encontrada."
        )

    if (
        df_rms["CO_MUNICIPIO"]
        .isin(CODIGOS_RMS)
        .all()
        is False
    ):
        raise ValueError(
            "Foram encontrados municípios "
            "fora do recorte da RMS."
        )

    if df_rms[
        [
            "NU_ANO_CENSO",
            "CO_ENTIDADE",
        ]
    ].duplicated().any():
        raise ValueError(
            "Existem escolas duplicadas "
            "para o mesmo ano e código INEP."
        )

    anos = set(
        df_rms["NU_ANO_CENSO"]
        .dropna()
        .astype(int)
    )

    if anos != {ano}:
        raise ValueError(
            "Ano encontrado no arquivo "
            f"não corresponde à edição {ano}: "
            f"{sorted(anos)}"
        )

    # Converte indicadores 0/1 para boolean.
    colunas_booleanas = [
        "IN_COMUM_MEDIO_MEDIO",
        "IN_COMUM_MEDIO_INTEGRADO",
        "IN_COMUM_MEDIO_FIC",
        "IN_COMUM_MEDIO_NORMAL",
        "IN_ITINERARIO_TECN_PROF",
    ]

    for coluna in colunas_booleanas:

        df_rms[coluna] = (
            df_rms[coluna]
            .map(
                {
                    0: False,
                    1: True,
                    0.0: False,
                    1.0: True,
                }
            )
        )

    df_rms.columns = [
        coluna.lower()
        for coluna in df_rms.columns
    ]

    print(
        "Escolas encontradas na RMS: "
        f"{len(df_rms)}"
    )

    print(
        "Validação concluída com sucesso."
    )

    return df_rms


# ============================================================
# FONTE
# ============================================================

def obter_id_fonte(
    conexao,
) -> int:

    resultado = conexao.execute(
        text(
            """
            SELECT id_fonte
            FROM fonte_dados
            WHERE no_orgao = 'INEP'
              AND no_fonte = 'Censo Escolar'
            LIMIT 1
            """
        )
    ).scalar()

    if resultado is not None:
        return resultado

    return conexao.execute(
        text(
            """
            INSERT INTO fonte_dados (
                no_orgao,
                no_fonte,
                ds_url_oficial,
                ds_periodicidade,
                ds_tipo_fonte,
                ds_observacao
            )
            VALUES (
                'INEP',
                'Censo Escolar',
                :url,
                'Anual',
                'OFICIAL_PRINCIPAL',
                'Fonte mestre das escolas '
                'de educação básica do Veltis.'
            )
            RETURNING id_fonte
            """
        ),
        {
            "url": PAGINA_OFICIAL
        },
    ).scalar_one()


# ============================================================
# HASH JÁ PROCESSADO
# ============================================================

def hash_ja_processado(
    conexao,
    id_fonte: int,
    hash_arquivo: str,
) -> bool:

    resultado = conexao.execute(
        text(
            """
            SELECT 1
            FROM controle_ingestao
            WHERE id_fonte = :id_fonte
              AND ds_hash_sha256 = :hash
              AND ds_status = 'CONCLUIDA'
            LIMIT 1
            """
        ),
        {
            "id_fonte": id_fonte,
            "hash": hash_arquivo,
        },
    ).first()

    return resultado is not None


# ============================================================
# CARGA
# ============================================================

def carregar_banco(
    df: pd.DataFrame,
    ano: int,
    hash_arquivo: str,
    nome_arquivo: str,
    quantidade_lida: int,
) -> None:

    registros = (
        df.where(
            pd.notnull(df),
            None,
        )
        .to_dict(
            orient="records"
        )
    )

    with engine.begin() as conexao:

        id_fonte = obter_id_fonte(
            conexao
        )

        if hash_ja_processado(
            conexao,
            id_fonte,
            hash_arquivo,
        ):

            print(
                "Esta versão do Censo Escolar "
                "já foi processada."
            )

            return

        sql = text(
            """
            INSERT INTO inep_escola (
                nu_ano_censo,
                co_entidade,
                no_entidade,
                co_municipio,
                no_municipio,
                sg_uf,
                tp_dependencia,
                tp_localizacao,
                tp_situacao_funcionamento,
                in_comum_medio_medio,
                in_comum_medio_integrado,
                in_comum_medio_fic,
                in_comum_medio_normal,
                in_itinerario_tecn_prof
            )
            VALUES (
                :nu_ano_censo,
                :co_entidade,
                :no_entidade,
                :co_municipio,
                :no_municipio,
                :sg_uf,
                :tp_dependencia,
                :tp_localizacao,
                :tp_situacao_funcionamento,
                :in_comum_medio_medio,
                :in_comum_medio_integrado,
                :in_comum_medio_fic,
                :in_comum_medio_normal,
                :in_itinerario_tecn_prof
            )

            ON CONFLICT (
                nu_ano_censo,
                co_entidade
            )

            DO UPDATE SET
                no_entidade =
                    EXCLUDED.no_entidade,

                co_municipio =
                    EXCLUDED.co_municipio,

                no_municipio =
                    EXCLUDED.no_municipio,

                sg_uf =
                    EXCLUDED.sg_uf,

                tp_dependencia =
                    EXCLUDED.tp_dependencia,

                tp_localizacao =
                    EXCLUDED.tp_localizacao,

                tp_situacao_funcionamento =
                    EXCLUDED.tp_situacao_funcionamento,

                in_comum_medio_medio =
                    EXCLUDED.in_comum_medio_medio,

                in_comum_medio_integrado =
                    EXCLUDED.in_comum_medio_integrado,

                in_comum_medio_fic =
                    EXCLUDED.in_comum_medio_fic,

                in_comum_medio_normal =
                    EXCLUDED.in_comum_medio_normal,

                in_itinerario_tecn_prof =
                    EXCLUDED.in_itinerario_tecn_prof
            """
        )

        conexao.execute(
            sql,
            registros,
        )

        conexao.execute(
            text(
                """
                INSERT INTO controle_ingestao (
                    id_fonte,
                    co_periodo_referencia,
                    ds_versao,
                    no_arquivo_origem,
                    dt_obtencao,
                    dt_processamento,
                    ds_hash_sha256,
                    qt_registros_lidos,
                    qt_registros_carregados,
                    qt_registros_rejeitados,
                    ds_status,
                    ds_observacao
                )
                VALUES (
                    :id_fonte,
                    :periodo,
                    :versao,
                    :arquivo,
                    CURRENT_DATE,
                    :processamento,
                    :hash,
                    :lidos,
                    :carregados,
                    0,
                    'CONCLUIDA',
                    :observacao
                )
                """
            ),
            {
                "id_fonte": id_fonte,
                "periodo": str(ano),
                "versao": (
                    f"Censo Escolar {ano}"
                ),
                "arquivo": nome_arquivo,
                "processamento": (
                    datetime.now()
                ),
                "hash": hash_arquivo,
                "lidos": quantidade_lida,
                "carregados": len(df),
                "observacao": (
                    "Tabela de escolas filtrada "
                    "para os 27 municípios da RMS."
                ),
            },
        )

    print(
        "INEP_ESCOLA atualizada com sucesso."
    )


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def executar_pipeline() -> None:

    print("")
    print("========================================")
    print("VELTIS - CENSO ESCOLAR / INEP")
    print("========================================")
    print("")

    ano, url = descobrir_edicao()

    caminho_zip = baixar_pacote(
        ano,
        url,
    )

    hash_arquivo = calcular_hash(
        caminho_zip
    )

    print(
        f"SHA-256: {hash_arquivo}"
    )

    nome_csv = localizar_csv_escolas(
        caminho_zip
    )

    df = ler_escolas(
        caminho_zip,
        nome_csv,
    )

    quantidade_lida = len(df)

    df_rms = processar_escolas(
        df,
        ano,
    )

    carregar_banco(
        df=df_rms,
        ano=ano,
        hash_arquivo=hash_arquivo,
        nome_arquivo=(
            caminho_zip.name
        ),
        quantidade_lida=quantidade_lida,
    )

    print("")
    print("========================================")
    print("PIPELINE CENSO ESCOLAR CONCLUÍDA")
    print("========================================")
    print("")


if __name__ == "__main__":
    executar_pipeline()