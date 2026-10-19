"""Pipeline 5 - Localização das escolas -> ESCOLA_LOCALIZACAO.

Fontes complementares, usadas para ENRIQUECER as escolas do Censo
Escolar (que não traz endereço nem coordenadas):
    1. INEP - Catálogo de Escolas   (data/raw/inep/catalogo_escolas/)
    2. SEDUC-SP - Escolas Ativas    (data/raw/seduc_sp/)

Regras do projeto:
  - O Censo Escolar define o universo: só entram códigos que existem em
    INEP_ESCOLA. Escolas só do Catálogo NÃO viram escolas novas.
  - Uma linha por escola, ano e fonte. Coordenada ausente fica NULL;
    nada é inventado. Coordenada fora de SP é descartada e contada.
  - TP_METODO_LOCALIZACAO: COORDENADA_OFICIAL quando há ponto;
    ENDERECO_OFICIAL quando só há endereço.
  - Pontos que caem fora do polígono do município da escola são
    mantidos e contados na observação da carga (a view os sinaliza).

Se a pasta de uma fonte estiver vazia, ela é pulada com um aviso.

Executar sozinho:  python -m src.collectors.localizacao_escolas [--forcar]
"""

import argparse
import csv
import io
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config.edicoes import ANO_CENSO_ESCOLAR
from src.config.fontes_localizacao import FONTES_LOCALIZACAO, LIMITES_SP
from src.loaders.carga import para_registros, upsert
from src.loaders.ingestao import Fonte, carga, hash_arquivo
from src.transforms import codigos as conv
from src.validators import basicos as validar


EXTENSOES = {".csv", ".txt", ".xlsx", ".xls"}
REGEX_CEP = re.compile(r"\b(\d{5})-?(\d{3})\b")


# ============================================================
# LEITURA DO ARQUIVO EXPORTADO
# ============================================================

def arquivo_mais_recente(pasta: Path) -> Path | None:
    if not pasta.exists():
        return None

    arquivos = [
        p for p in pasta.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSOES and not p.name.startswith(".")
    ]

    return max(arquivos, key=lambda p: p.stat().st_mtime) if arquivos else None


def _decodificar(bruto: bytes) -> str:
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            return bruto.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível identificar a codificação do arquivo.")


def ler_arquivo(caminho: Path) -> pd.DataFrame:
    """Lê CSV (separador e codificação detectados) ou Excel, tudo como texto."""

    if caminho.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(caminho, dtype=str)
        return df.fillna("")

    conteudo = _decodificar(caminho.read_bytes())
    amostra = conteudo[:20000]

    try:
        separador = csv.Sniffer().sniff(amostra, delimiters=";,\t|").delimiter
    except csv.Error:
        separador = ";"

    return pd.read_csv(
        io.StringIO(conteudo),
        sep=separador,
        dtype=str,
        keep_default_na=False,
    )


def mapear_colunas(df: pd.DataFrame, aliases: dict[str, list[str]], origem: str) -> dict[str, str]:
    """Campo lógico -> nome real da coluna no arquivo."""

    normalizadas = {conv.normalizar_nome(c): c for c in df.columns}
    mapa = {}

    for campo, nomes in aliases.items():
        for nome in nomes:
            if nome in normalizadas:
                mapa[campo] = normalizadas[nome]
                break

    if "codigo" not in mapa:
        raise validar.ErroValidacao(
            f"{origem}: não encontrei a coluna do código INEP da escola. "
            f"Colunas do arquivo: {list(df.columns)}. "
            "Acrescente o nome certo em src/config/fontes_localizacao.py."
        )

    tem_coordenada = "latitude" in mapa and "longitude" in mapa
    if not tem_coordenada and "endereco" not in mapa:
        raise validar.ErroValidacao(
            f"{origem}: o arquivo não tem latitude/longitude nem endereço "
            f"reconhecíveis. Colunas do arquivo: {list(df.columns)}."
        )

    return mapa


# ============================================================
# TRANSFORMAÇÃO
# ============================================================

def _coluna(df: pd.DataFrame, mapa: dict, campo: str) -> pd.Series:
    if campo in mapa:
        return df[mapa[campo]]
    return pd.Series([""] * len(df), index=df.index)


def coordenada_valida(lat, lon) -> bool:
    if lat is None or lon is None:
        return False

    return (
        LIMITES_SP["lat_min"] <= lat <= LIMITES_SP["lat_max"]
        and LIMITES_SP["lon_min"] <= lon <= LIMITES_SP["lon_max"]
    )


def montar_endereco(df: pd.DataFrame, mapa: dict) -> pd.Series:
    partes = [
        _coluna(df, mapa, "endereco"),
        _coluna(df, mapa, "numero"),
        _coluna(df, mapa, "complemento"),
        _coluna(df, mapa, "bairro"),
    ]

    def juntar(valores):
        logradouro, numero, complemento, bairro = (str(v).strip() for v in valores)
        if not logradouro:
            return None

        texto = f"{logradouro}, {numero}" if numero else logradouro
        if complemento:
            texto += f" - {complemento}"
        if bairro:
            texto += f" - {bairro}"

        return texto[:350]

    return pd.Series(
        [juntar(v) for v in zip(*partes, strict=True)], index=df.index, dtype=object
    )


def extrair_cep(cep_coluna, endereco) -> str | None:
    cep = conv.somente_digitos(cep_coluna, 8)
    if cep and len(cep.lstrip("0")) >= 5:
        return cep

    if endereco:
        achado = REGEX_CEP.search(str(endereco))
        if achado:
            return achado.group(1) + achado.group(2)

    return None


def processar_localizacoes(
    df: pd.DataFrame,
    mapa: dict,
    escolas_validas: set[int],
    ano: int,
    origem: str,
) -> tuple[pd.DataFrame, dict]:
    codigos = conv.para_inteiro(_coluna(df, mapa, "codigo"))
    df = df.assign(_codigo=codigos)

    no_universo = df[df["_codigo"].isin(escolas_validas)].copy()
    fora_do_universo = int(df["_codigo"].notna().sum() - len(no_universo))

    validar.sem_duplicidade(no_universo, ["_codigo"], origem)

    # Listas (e não Series) para o None não virar NaN.
    latitudes = [conv.para_coordenada(v) for v in _coluna(no_universo, mapa, "latitude")]
    longitudes = [conv.para_coordenada(v) for v in _coluna(no_universo, mapa, "longitude")]
    validas = [coordenada_valida(a, o) for a, o in zip(latitudes, longitudes, strict=True)]

    tinha_coordenada = [a is not None and o is not None for a, o in zip(latitudes, longitudes, strict=True)]
    descartadas = sum(1 for t, v in zip(tinha_coordenada, validas, strict=True) if t and not v)

    enderecos = montar_endereco(no_universo, mapa)
    ceps = [
        extrair_cep(c, e)
        for c, e in zip(_coluna(no_universo, mapa, "cep"), enderecos, strict=True)
    ]

    indice = no_universo.index
    lat_ok = [round(a, 7) if v else None for a, v in zip(latitudes, validas, strict=True)]
    lon_ok = [round(o, 7) if v else None for o, v in zip(longitudes, validas, strict=True)]

    saida = pd.DataFrame(
        {
            "nu_ano_censo": ano,
            "co_entidade": no_universo["_codigo"].astype("Int64"),
            "ds_endereco": conv.como_objeto(enderecos, indice),
            "nu_cep": conv.como_objeto(ceps, indice),
            "nu_telefone": conv.para_texto(_coluna(no_universo, mapa, "telefone"), 30),
            "vl_latitude": conv.como_objeto(lat_ok, indice),
            "vl_longitude": conv.como_objeto(lon_ok, indice),
            "geometry": conv.como_objeto(
                (f"POINT({o} {a})" if v else None for a, o, v in zip(lat_ok, lon_ok, validas, strict=True)),
                indice,
            ),
            "tp_metodo_localizacao": conv.como_objeto(
                (
                    "COORDENADA_OFICIAL" if v else ("ENDERECO_OFICIAL" if e else None)
                    for v, e in zip(validas, enderecos, strict=True)
                ),
                indice,
            ),
        },
        index=indice,
    )

    sem_nada = saida["tp_metodo_localizacao"].isna()
    saida = saida[~sem_nada].copy()

    resumo = {
        "linhas_arquivo": len(df),
        "fora_do_universo": fora_do_universo,
        "gravadas": len(saida),
        "com_coordenada": int((saida["tp_metodo_localizacao"] == "COORDENADA_OFICIAL").sum()),
        "coordenadas_descartadas": descartadas,
        "sem_endereco_nem_ponto": int(sem_nada.sum()),
    }

    return saida.reset_index(drop=True), resumo


# ============================================================
# CARGA
# ============================================================

def carregar_fonte(config: dict, forcar: bool = False) -> str:
    caminho = arquivo_mais_recente(config["pasta"])

    if caminho is None:
        print(
            f"AVISO: nenhum arquivo em {config['pasta']}. "
            f"Fonte '{config['nome']}' pulada."
        )
        return "PULADA"

    print(f"\n{config['nome']}: lendo {caminho.name}")

    fonte = Fonte(
        orgao=config["orgao"],
        nome=config["nome"],
        url_oficial=config["url"],
        periodicidade="Variável",
        tipo="OFICIAL_COMPLEMENTAR",
        observacao="Arquivo exportado manualmente e colocado em data/raw.",
    )

    with carga(
        fonte,
        periodo=str(ANO_CENSO_ESCOLAR),
        versao=f"Exportação {caminho.name}",
        arquivo=caminho.name,
        hash_arquivo=hash_arquivo(caminho),
        forcar=forcar,
    ) as ing:
        if ing is None:
            return "JA_CARREGADA"

        escolas_validas = set(
            ing.conexao.execute(
                text("SELECT co_entidade FROM inep_escola WHERE nu_ano_censo = :ano"),
                {"ano": ANO_CENSO_ESCOLAR},
            ).scalars()
        )

        if not escolas_validas:
            raise validar.ErroValidacao(
                "INEP_ESCOLA está vazia para o ano configurado; "
                "rode antes o pipeline do Censo Escolar."
            )

        df = ler_arquivo(caminho)
        mapa = mapear_colunas(df, config["colunas"], config["nome"])
        print(f"Colunas reconhecidas: {mapa}")

        saida, resumo = processar_localizacoes(
            df, mapa, escolas_validas, ANO_CENSO_ESCOLAR, config["nome"]
        )
        saida["id_fonte"] = ing.id_fonte
        saida["id_ingestao"] = ing.id_ingestao

        # Substitui a fonte inteira no ano (remove escolas que saíram do arquivo).
        ing.conexao.execute(
            text(
                "DELETE FROM escola_localizacao "
                "WHERE nu_ano_censo = :ano AND id_fonte = :fonte"
            ),
            {"ano": ANO_CENSO_ESCOLAR, "fonte": ing.id_fonte},
        )

        carregados = upsert(
            ing.conexao,
            "escola_localizacao",
            para_registros(saida),
            chave=["nu_ano_censo", "co_entidade", "id_fonte"],
            expressoes={"geometry": "ST_GeomFromText(:geometry, 4674)"},
        )

        fora_do_municipio = ing.conexao.execute(
            text(
                """
                SELECT COUNT(*)
                FROM escola_localizacao l
                JOIN inep_escola e USING (nu_ano_censo, co_entidade)
                JOIN ibge_municipios m ON m.cd_mun = e.co_municipio
                WHERE l.id_ingestao = :id
                  AND l.geometry IS NOT NULL
                  AND NOT ST_Intersects(m.geometry, l.geometry)
                """
            ),
            {"id": ing.id_ingestao},
        ).scalar_one()

        print(
            f"{config['nome']}: {resumo['gravadas']} escolas gravadas, "
            f"{resumo['com_coordenada']} com coordenada; "
            f"{resumo['coordenadas_descartadas']} coordenadas inválidas descartadas; "
            f"{fora_do_municipio} pontos fora do polígono do município; "
            f"{resumo['fora_do_universo']} códigos fora do Censo/RMS ignorados."
        )

        ing.registrar_contagens(
            lidos=resumo["linhas_arquivo"],
            carregados=carregados,
            rejeitados=resumo["coordenadas_descartadas"],
            observacao=(
                f"{resumo['com_coordenada']} com coordenada; "
                f"{fora_do_municipio} pontos fora do polígono do município; "
                f"{resumo['fora_do_universo']} códigos fora do Censo/RMS ignorados."
            ),
        )

    return "CARREGADA"


def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== LOCALIZAÇÃO DAS ESCOLAS (Catálogo INEP + SEDUC-SP) ===")

    for config in sorted(FONTES_LOCALIZACAO, key=lambda c: c["prioridade"]):
        carregar_fonte(config, forcar=forcar)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true")
    executar_pipeline(forcar=parser.parse_args().forcar)
