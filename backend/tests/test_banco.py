"""Testes de integração com um PostgreSQL + PostGIS VAZIO.

Só rodam se a variável VELTIS_TESTE_DATABASE_URL apontar para um banco
de teste descartável (NUNCA o Supabase de produção). Exemplo:

    VELTIS_TESTE_DATABASE_URL=postgresql+psycopg://postgres:senha@localhost:5432/veltis_teste
    pytest tests/test_banco.py

O banco precisa estar vazio; as migrations são aplicadas pelo teste.
"""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src import database, migrar


URL_TESTE = os.getenv("VELTIS_TESTE_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not URL_TESTE, reason="defina VELTIS_TESTE_DATABASE_URL para rodar"
)


@pytest.fixture(scope="module")
def engine():
    os.environ["DATABASE_URL"] = URL_TESTE
    database.get_engine.cache_clear()
    engine = database.get_engine()

    with engine.connect() as conexao:
        tabelas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'ibge_municipios'"
            )
        ).scalar_one()

    if tabelas:
        pytest.skip("o banco de teste não está vazio")

    migrar.aplicar_pendentes()
    yield engine
    database.get_engine.cache_clear()


def _municipio(conexao, codigo="3552205"):
    conexao.execute(
        text(
            "INSERT INTO ibge_municipios (cd_mun, nm_mun, geometry) VALUES "
            "(:c, 'Teste', ST_Multi(ST_GeomFromText("
            "'POLYGON((-47.5 -23.5,-47.4 -23.5,-47.4 -23.4,-47.5 -23.5))', 4674)))"
        ),
        {"c": codigo},
    )


def test_todas_as_migrations_aplicadas(engine):
    with engine.connect() as conexao:
        nomes = set(conexao.execute(text("SELECT no_arquivo FROM veltis_migracao")).scalars())

    esperados = {p.name for p in migrar.listar_arquivos()}
    assert nomes == esperados


def test_tabela_de_classificacoes_foi_unificada(engine):
    with engine.connect() as conexao:
        assert conexao.execute(text("SELECT to_regclass('ibge_demo_classif')")).scalar() is None


def test_rls_ligado_em_todas_as_tabelas_do_veltis(engine):
    with engine.connect() as conexao:
        sem_rls = conexao.execute(
            text(
                "SELECT relname FROM pg_class "
                "WHERE relnamespace = 'public'::regnamespace AND relkind = 'r' "
                "AND relname <> 'spatial_ref_sys' AND NOT relrowsecurity"
            )
        ).scalars().all()

    assert sem_rls == []


def test_valor_demografico_nao_duplica(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as conexao:
            _municipio(conexao)
            for _ in range(2):
                conexao.execute(
                    text(
                        "INSERT INTO ibge_demografico "
                        "(cd_mun, co_periodo, cd_agregado, cd_variavel, vl_indicador) "
                        "VALUES ('3552205', '2022', '4709', '93', 1)"
                    )
                )


def test_fonte_nao_duplica(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as conexao:
            for _ in range(2):
                conexao.execute(
                    text(
                        "INSERT INTO fonte_dados (no_orgao, no_fonte, ds_tipo_fonte) "
                        "VALUES ('X', 'Y', 'INTERNA')"
                    )
                )


def test_oferta_de_curso_nao_duplica(engine):
    with pytest.raises(IntegrityError):
        with engine.begin() as conexao:
            _municipio(conexao)
            conexao.execute(
                text(
                    "INSERT INTO mec_ies (nu_ano_censo, co_ies, no_ies, co_municipio_ies, "
                    "no_municipio_ies, sg_uf_ies, tp_organizacao_academica, tp_rede, "
                    "tp_categoria_administrativa) VALUES "
                    "(2024, 33, 'FATEC', '3552205', 'Sorocaba', 'SP', 3, 1, 2)"
                )
            )
            for _ in range(2):
                conexao.execute(
                    text(
                        "INSERT INTO mec_cursos (nu_ano_censo, tp_dimensao, co_ies, co_curso, "
                        "no_curso, co_municipio, in_gratuito, tp_modalidade_ensino, "
                        "tp_nivel_academico, qt_curso, qt_vg_total, qt_mat) VALUES "
                        "(2024, 1, 33, 1, 'ADS', '3552205', TRUE, 1, 1, 1, 40, 120)"
                    )
                )
