import hashlib
import json
from datetime import datetime

import requests
from sqlalchemy import text

from src.config.rms import CODIGOS_RMS
from src.database import engine


URL_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

AGREGADO = "4709"
VARIAVEL = "93"
PERIODO = "2022"


def montar_url() -> tuple[str, dict]:
    municipios = ",".join(CODIGOS_RMS)

    url = (
        f"{URL_BASE}/"
        f"{AGREGADO}/"
        f"periodos/{PERIODO}/"
        f"variaveis/{VARIAVEL}"
    )

    parametros = {
        "localidades": f"N6[{municipios}]"
    }

    return url, parametros


def consultar_sidra() -> list:
    url, parametros = montar_url()

    print("Consultando SIDRA...")
    print(f"Agregado: {AGREGADO}")
    print(f"Variável: {VARIAVEL}")
    print(f"Período: {PERIODO}")

    resposta = requests.get(
        url,
        params=parametros,
        timeout=120,
    )

    resposta.raise_for_status()

    dados = resposta.json()

    if not dados:
        raise ValueError(
            "A API do SIDRA não retornou dados."
        )

    print("Consulta realizada com sucesso.")

    return dados


def calcular_hash(dados: list) -> str:
    conteudo = json.dumps(
        dados,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")

    return hashlib.sha256(conteudo).hexdigest()


def obter_id_fonte(conexao) -> int:
    resultado = conexao.execute(
        text(
            """
            SELECT id_fonte
            FROM fonte_dados
            WHERE no_orgao = 'IBGE'
              AND no_fonte = 'SIDRA'
            LIMIT 1
            """
        )
    ).scalar()

    if resultado is not None:
        return resultado

    resultado = conexao.execute(
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
                'IBGE',
                'SIDRA',
                :url,
                'Variável',
                'OFICIAL_PRINCIPAL',
                'API de Dados Agregados do IBGE.'
            )
            RETURNING id_fonte
            """
        ),
        {
            "url": URL_BASE
        },
    )

    return resultado.scalar_one()


def hash_ja_processado(
    conexao,
    id_fonte: int,
    hash_dados: str,
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
            "hash": hash_dados,
        },
    ).first()

    return resultado is not None


def transformar(dados: list) -> list[dict]:
    registros = []

    variavel = dados[0]

    codigo_variavel = variavel["id"]
    nome_variavel = variavel["variavel"]
    unidade = variavel["unidade"]

    resultados = variavel["resultados"]

    for resultado in resultados:
        classificacoes = resultado["classificacoes"]

        if classificacoes:
            raise ValueError(
                "Esta consulta possui classificações. "
                "Vamos tratá-las na próxima etapa."
            )

        for serie in resultado["series"]:
            localidade = serie["localidade"]
            valores = serie["serie"]

            codigo_municipio = localidade["id"]

            if codigo_municipio not in CODIGOS_RMS:
                raise ValueError(
                    f"Município inesperado: {codigo_municipio}"
                )

            if PERIODO not in valores:
                raise ValueError(
                    f"Período {PERIODO} não encontrado "
                    f"para o município {codigo_municipio}."
                )

            valor_original = valores[PERIODO]

            if valor_original in (
                None,
                "",
                "-",
                "...",
            ):
                valor = None
            else:
                valor = float(valor_original)

            registros.append(
                {
                    "cd_mun": codigo_municipio,
                    "co_periodo": PERIODO,
                    "cd_agregado": AGREGADO,
                    "cd_variavel": codigo_variavel,
                    "no_variavel": nome_variavel,
                    "ds_unidade": unidade,
                    "vl_indicador": valor,
                }
            )

    return registros


def validar(registros: list[dict]) -> None:
    if len(registros) != 27:
        raise ValueError(
            f"Esperávamos 27 registros, "
            f"mas encontramos {len(registros)}."
        )

    codigos = {
        registro["cd_mun"]
        for registro in registros
    }

    faltantes = set(CODIGOS_RMS) - codigos

    if faltantes:
        raise ValueError(
            f"Municípios faltantes: {sorted(faltantes)}"
        )

    if len(codigos) != 27:
        raise ValueError(
            "Existem municípios duplicados."
        )

    print(
        "Validação concluída: "
        "27 municípios da RMS."
    )


def carregar_banco(
    registros: list[dict],
    hash_dados: str,
) -> None:

    with engine.begin() as conexao:

        id_fonte = obter_id_fonte(conexao)

        if hash_ja_processado(
            conexao,
            id_fonte,
            hash_dados,
        ):
            print(
                "Essa resposta do SIDRA "
                "já foi processada."
            )
            return

        # ----------------------------------------------------
        # Remove somente esta consulta específica
        # ----------------------------------------------------

        ids_existentes = conexao.execute(
            text(
                """
                SELECT id_demografico
                FROM ibge_demografico
                WHERE cd_agregado = :agregado
                  AND cd_variavel = :variavel
                  AND co_periodo = :periodo
                  AND cd_mun = ANY(:municipios)
                """
            ),
            {
                "agregado": AGREGADO,
                "variavel": VARIAVEL,
                "periodo": PERIODO,
                "municipios": CODIGOS_RMS,
            },
        ).scalars().all()

        if ids_existentes:
            conexao.execute(
                text(
                    """
                    DELETE FROM ibge_demo_classif
                    WHERE id_demografico = ANY(:ids)
                    """
                ),
                {
                    "ids": ids_existentes
                },
            )

            conexao.execute(
                text(
                    """
                    DELETE FROM ibge_demografico
                    WHERE id_demografico = ANY(:ids)
                    """
                ),
                {
                    "ids": ids_existentes
                },
            )

        # ----------------------------------------------------
        # Inserção
        # ----------------------------------------------------

        for registro in registros:
            conexao.execute(
                text(
                    """
                    INSERT INTO ibge_demografico (
                        cd_mun,
                        co_periodo,
                        cd_agregado,
                        cd_variavel,
                        no_variavel,
                        ds_unidade,
                        vl_indicador
                    )
                    VALUES (
                        :cd_mun,
                        :co_periodo,
                        :cd_agregado,
                        :cd_variavel,
                        :no_variavel,
                        :ds_unidade,
                        :vl_indicador
                    )
                    """
                ),
                registro,
            )

        # ----------------------------------------------------
        # Controle de ingestão
        # ----------------------------------------------------

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
                    :origem,
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
                "periodo": PERIODO,
                "versao": (
                    f"SIDRA agregado {AGREGADO} "
                    f"variável {VARIAVEL}"
                ),
                "origem": (
                    f"API_SIDRA_{AGREGADO}_"
                    f"{VARIAVEL}_{PERIODO}.json"
                ),
                "processamento": datetime.now(),
                "hash": hash_dados,
                "lidos": len(registros),
                "carregados": len(registros),
                "observacao": (
                    "Consulta automática via API SIDRA "
                    "para os 27 municípios da RMS."
                ),
            },
        )

    print(
        "IBGE_DEMOGRAFICO atualizado com sucesso."
    )


def executar_pipeline() -> None:
    print("")
    print("========================================")
    print("VELTIS - SIDRA / IBGE")
    print("========================================")
    print("")

    dados = consultar_sidra()

    hash_dados = calcular_hash(dados)

    print(f"SHA-256: {hash_dados}")

    registros = transformar(dados)

    validar(registros)

    carregar_banco(
        registros,
        hash_dados,
    )

    print("")
    print("========================================")
    print("PIPELINE SIDRA CONCLUÍDA")
    print("========================================")
    print("")


if __name__ == "__main__":
    executar_pipeline()