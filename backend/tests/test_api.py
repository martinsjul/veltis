"""Testes da API.

1. Testes sem banco (rodam sempre): validação dos filtros, busca sem
   acento, GeoJSON, paginação e a mensagem de banco fora do ar.

2. Testes com banco (só com VELTIS_TESTE_API=1): chamam cada endereço
   no banco do .env. Como a API só lê, é seguro rodar até no Supabase:

       VELTIS_TESTE_API=1 pytest tests/test_api.py      (Linux/Mac)
       set VELTIS_TESTE_API=1 && pytest tests/test_api.py   (Windows cmd)
"""

import json
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from api.db import conexao
from api.filtros import Condicoes, Paginacao, padrao_busca, pagina_de, sem_acento_sql
from api.geojson import colecao
from api.main import app


# ------------------------------------------------------------ sem banco

@pytest.fixture
def cliente_sem_banco():
    def conexao_falsa():
        # A validação recusa o pedido antes de qualquer consulta.
        yield None

    app.dependency_overrides[conexao] = conexao_falsa
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "url",
    [
        "/municipios/abc",
        "/municipios/123",
        "/municipios?detalhe=enorme",
        "/escolas?municipio=sorocaba",
        "/escolas?dependencia=particular",
        "/escolas?busca=a",
        "/escolas/sem-localizacao?por_pagina=1000",
        "/escolas/sem-localizacao?pagina=0",
        "/cursos-superiores?modalidade=semipresencial",
        "/cursos-superiores?grau=doutorado",
        "/instituicoes?rede=mista",
        "/escolas/0",
    ],
)
def test_filtro_invalido_responde_422(cliente_sem_banco, url):
    assert cliente_sem_banco.get(url).status_code == 422


def test_banco_fora_do_ar_responde_503_sem_detalhe_tecnico():
    def conexao_quebrada():
        raise OperationalError("SELECT 1", {}, Exception("senha errada para o usuário x"))
        yield  # pragma: no cover

    app.dependency_overrides[conexao] = conexao_quebrada
    try:
        resposta = TestClient(app).get("/saude")
    finally:
        app.dependency_overrides.clear()

    assert resposta.status_code == 503
    assert "senha" not in resposta.text


def test_busca_ignora_acento_e_maiusculas():
    assert padrao_busca("  São ROQUE ") == "%sao roque%"


def test_busca_escapa_curingas_do_like():
    assert padrao_busca("50%_a\\b") == "%50\\%\\_a\\\\b%"


def test_sem_acento_sql_tem_listas_do_mesmo_tamanho():
    sql = sem_acento_sql("x")
    com, sem = sql.split("'")[1], sql.split("'")[3]
    assert len(com) == len(sem)


def test_condicoes_usam_parametros():
    c = Condicoes()
    c.adicionar("co_municipio = :m", m="3552205")
    c.busca(["no_entidade"], "Fatec")
    assert c.where.startswith("WHERE co_municipio = :m AND (")
    assert "Fatec" not in c.where
    assert c.params == {"m": "3552205", "busca": "%fatec%"}
    assert Condicoes().where == ""


def test_pagina_de_remove_total_dos_itens():
    itens = [{"a": 1, "_total": 7}, {"a": 2, "_total": 7}]
    resposta = pagina_de(itens, Paginacao(pagina=2, por_pagina=2))
    assert resposta == {"total": 7, "pagina": 2, "por_pagina": 2, "itens": [{"a": 1}, {"a": 2}]}
    assert pagina_de([], Paginacao(1, 50))["total"] == 0


def test_colecao_geojson():
    resposta = colecao(
        [{"id": 1, "nome": "A", "geometria": {"type": "Point", "coordinates": [-47.4, -23.5]}}],
        coluna_id="id",
        metadados={"total": 1},
    )
    corpo = json.loads(resposta.body)
    assert resposta.media_type == "application/geo+json"
    assert corpo["type"] == "FeatureCollection"
    assert corpo["features"][0] == {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-47.4, -23.5]},
        "properties": {"id": 1, "nome": "A"},
        "id": 1,
    }
    assert corpo["metadados"] == {"total": 1}


# ------------------------------------------------------------ com banco

com_banco = pytest.mark.skipif(
    os.getenv("VELTIS_TESTE_API") != "1", reason="defina VELTIS_TESTE_API=1 para rodar"
)


@pytest.fixture(scope="module")
def cliente():
    return TestClient(app)


@com_banco
def test_conexao_da_api_nao_grava(cliente):
    gerador = conexao()
    con = next(gerador)
    try:
        with pytest.raises(Exception, match="read-only"):
            con.execute(text("CREATE TEMP TABLE veltis_teste_escrita (x int)"))
    finally:
        gerador.close()


@com_banco
def test_saude(cliente):
    assert cliente.get("/saude").json() == {"status": "ok", "banco": "ok"}


@com_banco
def test_municipios_geojson(cliente):
    corpo = cliente.get("/municipios").json()
    assert corpo["type"] == "FeatureCollection"
    assert len(corpo["features"]) == 27
    assert corpo["features"][0]["geometry"]["type"] in {"Polygon", "MultiPolygon"}


@com_banco
def test_indicadores_e_ficha(cliente):
    assert len(cliente.get("/municipios/indicadores").json()) == 27

    ficha = cliente.get("/municipios/3552205").json()
    assert ficha["nm_mun"] == "Sorocaba"
    assert ficha["educacao"]["escolas_ativas"] > 0
    assert ficha["educacao"]["instituicoes_presenciais"] > 0

    assert cliente.get("/municipios/3550308").status_code == 404  # São Paulo não é da RMS


@com_banco
def test_escolas_mapa_e_ficha(cliente):
    corpo = cliente.get("/escolas?municipio=3552205").json()
    meta = corpo["metadados"]
    assert meta["no_mapa"] == len(corpo["features"])
    assert meta["total_filtrado"] == meta["no_mapa"] + meta["sem_coordenada"]
    assert all(f["properties"]["co_municipio"] == "3552205" for f in corpo["features"])

    if corpo["features"]:
        codigo = corpo["features"][0]["id"]
        ficha = cliente.get(f"/escolas/{codigo}").json()
        assert ficha["co_entidade"] == codigo
        assert isinstance(ficha["cursos_tecnicos"], list)

    assert cliente.get("/escolas/1").status_code == 404


@com_banco
def test_escolas_sem_localizacao_paginadas(cliente):
    pagina = cliente.get("/escolas/sem-localizacao?por_pagina=5").json()
    assert len(pagina["itens"]) <= 5
    assert pagina["total"] >= len(pagina["itens"])


@com_banco
def test_cursos(cliente):
    tecnicos = cliente.get("/cursos-tecnicos?incluir_magisterio=false").json()
    assert not any(i["e_normal_magisterio"] for i in tecnicos["itens"])

    superiores = cliente.get("/cursos-superiores?modalidade=presencial&busca=fatec").json()
    assert superiores["total"] > 0
    assert all(i["e_presencial"] for i in superiores["itens"])

    instituicoes = cliente.get("/instituicoes?modalidade=presencial&por_pagina=500").json()
    assert instituicoes["total"] > 0
    assert all(i["qt_cursos_presenciais"] > 0 for i in instituicoes["itens"])


@com_banco
def test_filtros_e_fontes(cliente):
    filtros = cliente.get("/filtros").json()
    assert len(filtros["municipios"]) == 27
    assert {o["valor"] for o in filtros["dependencias"]} == {"federal", "estadual", "municipal", "privada"}
    assert isinstance(cliente.get("/fontes").json(), list)
