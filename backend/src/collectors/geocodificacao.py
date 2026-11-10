"""Pipeline 5 - Geocodificação das escolas sem coordenada -> ESCOLA_LOCALIZACAO.

Algumas escolas têm endereço (Catálogo INEP ou SEDUC-SP), mas não têm
latitude/longitude. Esta etapa calcula o ponto a partir do endereço com
o geocodebr (Ipea), que procura o endereço no CNEFE do IBGE (Censo 2022).

    - Gratuito, sem limite e sem chave: roda no próprio computador.
    - Na primeira vez baixa os dados do CNEFE (~1 GB) para o cache do usuário.
    - Só entram pontos com precisão de número ou de rua (nunca o centro
      do CEP, do bairro ou do município) e que caem dentro do município.
    - Coordenada oficial tem sempre prioridade: aqui só entra quem não tem.

Executar sozinho:  python -m src.collectors.geocodificacao [--forcar]
"""

import argparse
import re
import unicodedata
from importlib.metadata import PackageNotFoundError, version

import pandas as pd
from sqlalchemy import text

from src.config.edicoes import ANO_CENSO_ESCOLAR
from src.loaders.carga import para_registros, upsert
from src.loaders.ingestao import Fonte, carga, hash_json
from src.validators import basicos as validar


FONTE = Fonte(
    orgao="IBGE",
    nome="CNEFE 2022 - geocodificação (geocodebr/Ipea)",
    url_oficial="https://github.com/ipea/geocodebr",
    periodicidade="Variável",
    tipo="OFICIAL_COMPLEMENTAR",
    observacao=(
        "Ponto calculado a partir do endereço oficial da escola, procurando-o no "
        "Cadastro Nacional de Endereços para Fins Estatísticos (IBGE, Censo 2022)."
    ),
)

# Precisões aceitas e o maior desvio (metros) tolerado para cada uma.
PRECISOES_ACEITAS = {
    "numero": 500,
    "numero_aproximado": 500,
    "logradouro": 1000,
}

REGEX_CEP = re.compile(r"(\d{5})-?(\d{3})")
REGEX_NUMERO = re.compile(r"^\s*(?:N[º°O.]?\s*)?(\d[\d.]*)", re.IGNORECASE)
REGEX_SEM_NUMERO = re.compile(r"^\s*(S\s*/?\s*N\.?|SN|SEM N[UÚ]MERO)\b", re.IGNORECASE)


# ------------------------------------------------------------
# Endereço em texto -> campos separados
# ------------------------------------------------------------

def separar_endereco(endereco: str | None, cep: str | None = None) -> dict:
    """Separa logradouro, número, bairro e CEP de um endereço em texto.

    Formatos tratados:
        Catálogo INEP: "RUA NATAL, 340 JARDIM PAULISTANO. 18040-000 Sorocaba - SP"
        SEDUC-SP:      "RUA NATAL, 340 - CASA 2 - JARDIM PAULISTANO"
    """

    vazio = {"logradouro": None, "numero": None, "localidade": None, "cep": None}
    if not isinstance(endereco, str) or not endereco.strip():
        return vazio

    texto = endereco.strip()

    cep_digitos = re.sub(r"\D", "", cep if isinstance(cep, str) else "")
    achado = REGEX_CEP.search(texto)
    if achado:
        cep_digitos = cep_digitos or achado.group(1) + achado.group(2)
        texto = texto[: achado.start()]
    texto = texto.strip(" .-,")

    if "," in texto:
        logradouro, resto = texto.split(",", 1)
    else:
        logradouro, resto = texto, ""

    numero = None
    resto = resto.strip()
    if m := REGEX_SEM_NUMERO.match(resto):
        resto = resto[m.end():]
    elif m := REGEX_NUMERO.match(resto):
        numero = int(m.group(1).replace(".", ""))
        resto = resto[m.end():]

    partes = [p.strip(" .-,") for p in re.split(r"\s+-\s+", resto) if p.strip(" .-,")]
    # No formato SEDUC o bairro é a última parte; no Catálogo, o único texto.
    localidade = partes[-1] if partes else None

    return {
        "logradouro": logradouro.strip(" .-,") or None,
        "numero": numero if numero else None,
        "localidade": localidade,
        "cep": cep_digitos if len(cep_digitos) == 8 else None,
    }


def _sem_acento(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in normalizado if not unicodedata.combining(c)).upper()


# ------------------------------------------------------------
# Geocodificação
# ------------------------------------------------------------

def geocodificar(enderecos: pd.DataFrame) -> pd.DataFrame:
    """Chama o geocodebr. Entrada: id, logradouro, numero, cep, localidade, municipio."""

    import polars as pl
    from geocodebr import definir_campos, geocode

    entrada = pl.from_pandas(
        enderecos.assign(estado="SP", numero=enderecos["numero"].astype("Int64"))
    )
    campos = definir_campos(
        logradouro="logradouro",
        numero="numero",
        cep="cep",
        localidade="localidade",
        municipio="municipio",
        estado="estado",
    )
    resultado = geocode(
        enderecos=entrada,
        campos_endereco=campos,
        resultado_completo=False,
        resolver_empates=True,
        verboso=False,
    )
    return resultado.to_pandas()


def selecionar_pontos(resultado: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Mantém só os pontos com precisão aceita e desvio dentro do limite.

    Devolve (aceitos, contagem por motivo de recusa).
    """

    limite = resultado["precisao"].map(PRECISOES_ACEITAS)
    tem_ponto = resultado["lat"].notna() & resultado["lon"].notna()
    precisao_ok = limite.notna()
    desvio_ok = resultado["desvio_metros"].fillna(10**9) <= limite.fillna(-1)

    motivo = pd.Series("aceito", index=resultado.index)
    motivo[~tem_ponto] = "endereço não encontrado"
    motivo[tem_ponto & ~precisao_ok] = "só achou o CEP, o bairro ou o município"
    motivo[tem_ponto & precisao_ok & ~desvio_ok] = "desvio grande demais"

    return resultado[motivo == "aceito"].copy(), motivo.value_counts()


# ------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------

SQL_ESCOLAS_SEM_PONTO = """
SELECT DISTINCT ON (e.co_entidade)
    e.co_entidade, e.co_municipio, m.nm_mun AS municipio,
    l.ds_endereco, l.nu_cep
FROM inep_escola e
JOIN ibge_municipios m ON m.cd_mun = e.co_municipio
JOIN escola_localizacao l
  ON l.nu_ano_censo = e.nu_ano_censo AND l.co_entidade = e.co_entidade
JOIN fonte_dados f ON f.id_fonte = l.id_fonte
WHERE e.nu_ano_censo = :ano
  AND l.ds_endereco IS NOT NULL
  AND l.tp_metodo_localizacao <> 'GEOCODIFICADO'
  AND NOT EXISTS (
      SELECT 1 FROM escola_localizacao o
      WHERE o.nu_ano_censo = e.nu_ano_censo AND o.co_entidade = e.co_entidade
        AND o.geometry IS NOT NULL AND o.tp_metodo_localizacao <> 'GEOCODIFICADO'
  )
ORDER BY e.co_entidade, (f.no_orgao = 'INEP') DESC
"""


def _versao_geocodebr() -> str:
    try:
        return version("geocodebr")
    except PackageNotFoundError:
        raise RuntimeError(
            "O pacote geocodebr não está instalado. Rode: pip install -r requirements.txt"
        ) from None


def executar_pipeline(forcar: bool = False) -> None:
    print("\n=== GEOCODIFICAÇÃO DAS ESCOLAS SEM COORDENADA (IBGE CNEFE / geocodebr) ===")
    versao_pacote = _versao_geocodebr()

    from src.database import get_engine

    with get_engine().connect() as conexao:
        escolas = pd.read_sql(text(SQL_ESCOLAS_SEM_PONTO), conexao, params={"ano": ANO_CENSO_ESCOLAR})

    if escolas.empty:
        print("Nenhuma escola com endereço e sem coordenada oficial. Nada a fazer.")
        return

    # A versão "lógica" da carga = endereços de entrada + versão do pacote.
    assinatura = hash_json(
        {"geocodebr": versao_pacote, "enderecos": escolas.astype(str).values.tolist()}
    )

    with carga(
        FONTE,
        periodo=str(ANO_CENSO_ESCOLAR),
        versao=f"geocodebr {versao_pacote} sobre CNEFE 2022",
        arquivo="escolas_sem_coordenada",
        hash_arquivo=assinatura,
        forcar=forcar,
    ) as ing:
        if ing is None:
            return

        campos = pd.DataFrame(
            [separar_endereco(e, c) for e, c in zip(escolas["ds_endereco"], escolas["nu_cep"], strict=True)],
            index=escolas.index,
        )
        entrada = pd.concat([escolas[["co_entidade", "municipio"]], campos], axis=1)
        entrada["municipio"] = entrada["municipio"].map(_sem_acento)
        entrada = entrada[entrada["logradouro"].notna()]

        print(f"{len(escolas)} escolas sem coordenada oficial e com endereço; geocodificando...")
        resultado = geocodificar(entrada)
        aceitos, motivos = selecionar_pontos(resultado)

        aceitos = aceitos.merge(
            escolas[["co_entidade", "co_municipio", "ds_endereco", "nu_cep"]], on="co_entidade"
        )
        saida = pd.DataFrame(
            {
                "nu_ano_censo": ANO_CENSO_ESCOLAR,
                "co_entidade": aceitos["co_entidade"].astype("int64"),
                "ds_endereco": aceitos["ds_endereco"],
                "nu_cep": aceitos["nu_cep"],
                "nu_telefone": None,
                "vl_latitude": aceitos["lat"].round(7),
                "vl_longitude": aceitos["lon"].round(7),
                "geometry": [f"POINT({x} {y})" for x, y in zip(aceitos["lon"], aceitos["lat"], strict=True)],
                "id_fonte": ing.id_fonte,
                "tp_metodo_localizacao": "GEOCODIFICADO",
                "ds_precisao": aceitos["precisao"],
                "vl_desvio_metros": aceitos["desvio_metros"].round().astype("Int64"),
                "id_ingestao": ing.id_ingestao,
            }
        )
        validar.sem_duplicidade(saida, ["co_entidade"], "Geocodificação")

        # Substitui os pontos geocodificados do ano (recalcula do zero).
        ing.conexao.execute(
            text("DELETE FROM escola_localizacao WHERE nu_ano_censo = :ano AND id_fonte = :fonte"),
            {"ano": ANO_CENSO_ESCOLAR, "fonte": ing.id_fonte},
        )
        carregados = upsert(
            ing.conexao,
            "escola_localizacao",
            para_registros(saida),
            chave=["nu_ano_censo", "co_entidade", "id_fonte"],
            expressoes={"geometry": "ST_GeomFromText(:geometry, 4674)"},
        )

        # Ponto fora do município = endereço casou com outra cidade: descarta.
        fora = ing.conexao.execute(
            text(
                """
                DELETE FROM escola_localizacao l
                USING inep_escola e, ibge_municipios m
                WHERE l.id_ingestao = :id
                  AND e.nu_ano_censo = l.nu_ano_censo AND e.co_entidade = l.co_entidade
                  AND m.cd_mun = e.co_municipio
                  AND NOT ST_Intersects(m.geometry, l.geometry)
                RETURNING l.co_entidade
                """
            ),
            {"id": ing.id_ingestao},
        ).fetchall()

        gravados = carregados - len(fora)
        por_precisao = saida[~saida["co_entidade"].isin([f[0] for f in fora])]["ds_precisao"].value_counts()
        resumo_motivos = {k: int(v) for k, v in motivos.items() if k != "aceito"}
        if fora:
            resumo_motivos["ponto fora do município"] = len(fora)

        print(
            f"{gravados} escolas ganharam ponto {por_precisao.to_dict()}; "
            f"sem ponto: {resumo_motivos or 'nenhuma'}."
        )
        ing.registrar_contagens(
            lidos=len(escolas),
            carregados=gravados,
            rejeitados=len(escolas) - gravados,
            observacao=(
                f"Precisão: {por_precisao.to_dict()}. Sem ponto: {resumo_motivos}. "
                f"geocodebr {versao_pacote}."
            ),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar", action="store_true")
    executar_pipeline(forcar=parser.parse_args().forcar)
