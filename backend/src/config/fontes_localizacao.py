"""Mapeamento de colunas das fontes de localização das escolas.

O Catálogo de Escolas (INEP) e a base Escolas Ativas (SEDUC-SP) não têm
download automático: os arquivos são exportados à mão e colocados em
data/raw. Como o cabeçalho pode variar entre exportações, cada campo
aceita vários nomes. A comparação ignora acentos, maiúsculas e
pontuação ("Código INEP" == "codigo_inep").

Se a carga disser que não encontrou uma coluna, acrescente aqui o nome
que aparece no cabeçalho do seu arquivo.
"""

from pathlib import Path

from src.config.edicoes import URL_CATALOGO_ESCOLAS, URL_SEDUC_ESCOLAS


BASE_DIR = Path(__file__).resolve().parents[2]

FONTES_LOCALIZACAO = [
    {
        "chave": "catalogo",
        "orgao": "INEP",
        "nome": "Catálogo de Escolas",
        "url": URL_CATALOGO_ESCOLAS,
        "pasta": BASE_DIR / "data" / "raw" / "inep" / "catalogo_escolas",
        # Ordem de prioridade quando a escola tem ponto nas duas fontes.
        "prioridade": 1,
        "colunas": {
            "codigo": ["codigo_inep", "co_entidade", "cod_inep", "codigo_da_escola"],
            "latitude": ["latitude", "lat", "vl_latitude"],
            "longitude": ["longitude", "long", "lon", "lng", "vl_longitude"],
            "endereco": ["endereco", "ds_endereco", "logradouro"],
            "telefone": ["telefone", "nu_telefone", "fone"],
            "cep": ["cep", "nu_cep"],
        },
    },
    {
        "chave": "seduc",
        "orgao": "SEDUC-SP",
        "nome": "Escolas Ativas - Endereços",
        "url": URL_SEDUC_ESCOLAS,
        "pasta": BASE_DIR / "data" / "raw" / "seduc_sp",
        "prioridade": 2,
        "colunas": {
            "codigo": ["codescmec", "cod_esc_mec", "codigo_mec", "co_entidade", "codigo_inep"],
            "latitude": ["ds_latitude", "latitude", "lat"],
            "longitude": ["ds_longitude", "longitude", "long", "lon"],
            "endereco": ["endesc", "endereco", "ds_endereco", "logradouro"],
            "numero": ["numesc", "numero", "nr_endereco", "num"],
            "complemento": ["complemento", "compl"],
            "bairro": ["baiesc", "bairro"],
            "cep": ["cep", "nu_cep"],
            "telefone": ["fone1", "telefone", "fone"],
        },
    },
]

# Caixa que contém todo o estado de SP (com folga). Ponto fora dela é
# tratado como coordenada inválida e não é gravado.
LIMITES_SP = {
    "lat_min": -25.5,
    "lat_max": -19.5,
    "lon_min": -53.5,
    "lon_max": -44.0,
}
