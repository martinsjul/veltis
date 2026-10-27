"""Relatório de qualidade do banco depois das cargas.

Confere contagens e regras de consistência que não dependem da edição
dos dados. Imprime OK/ATENÇÃO/ERRO e devolve False se houver ERRO.

    python -m src.verificar
"""

from sqlalchemy import text

from src.database import get_engine


# (descrição, SQL que devolve um número, regra, nível se a regra falhar)
VERIFICACOES = [
    ("Municípios da RMS carregados",
     "SELECT COUNT(*) FROM ibge_municipios", lambda n: n == 27, "ERRO"),
    ("Geometrias municipais inválidas",
     "SELECT COUNT(*) FROM ibge_municipios WHERE NOT ST_IsValid(geometry)",
     lambda n: n == 0, "ERRO"),
    ("Municípios com população 2022 (SIDRA 4709)",
     "SELECT COUNT(*) FROM ibge_demografico WHERE cd_agregado = '4709' "
     "AND cd_variavel = '93' AND ds_chave_classificacao = ''",
     lambda n: n == 27, "ERRO"),
    ("Municípios onde total da 9514 difere da 4709",
     """
     SELECT COUNT(*) FROM ibge_demografico a
     JOIN ibge_demografico b ON b.cd_mun = a.cd_mun
     WHERE a.cd_agregado = '4709' AND a.cd_variavel = '93'
       AND b.cd_agregado = '9514'
       AND b.ds_chave_classificacao = '2:6794|286:113635|287:100362'
       AND a.vl_indicador <> b.vl_indicador
     """, lambda n: n == 0, "ERRO"),
    ("Valores demográficos (todas as tabelas SIDRA)",
     "SELECT COUNT(*) FROM ibge_demografico", lambda n: n > 0, "ERRO"),
    ("Escolas (Censo Escolar)",
     "SELECT COUNT(*) FROM inep_escola", lambda n: n > 0, "ERRO"),
    ("Escolas em atividade",
     "SELECT COUNT(*) FROM inep_escola WHERE tp_situacao_funcionamento = 1",
     lambda n: n > 0, "ERRO"),
    ("Cursos técnicos",
     "SELECT COUNT(*) FROM inep_curso_tecnico", lambda n: n > 0, "ATENÇÃO"),
    ("Escolas com localização (alguma fonte)",
     "SELECT COUNT(DISTINCT co_entidade) FROM escola_localizacao",
     lambda n: n > 0, "ATENÇÃO"),
    ("Escolas com ponto no mapa",
     "SELECT COUNT(*) FROM vw_escolas_mapa WHERE tem_coordenada",
     lambda n: n > 0, "ATENÇÃO"),
    ("Pontos de escola fora do polígono do município",
     "SELECT COUNT(*) FROM vw_escolas_mapa WHERE ponto_confere_municipio = FALSE",
     lambda n: n == 0, "ATENÇÃO"),
    ("IES com oferta na RMS",
     "SELECT COUNT(*) FROM mec_ies", lambda n: n > 0, "ERRO"),
    ("Ofertas de cursos superiores",
     "SELECT COUNT(*) FROM mec_cursos", lambda n: n > 0, "ERRO"),
    ("Ofertas presenciais",
     "SELECT COUNT(*) FROM mec_cursos WHERE tp_dimensao = 1", lambda n: n > 0, "ERRO"),
    ("Linhas de dados sem id_ingestao (sem rastreabilidade)",
     """
     SELECT (SELECT COUNT(*) FROM ibge_municipios WHERE id_ingestao IS NULL)
          + (SELECT COUNT(*) FROM ibge_demografico WHERE id_ingestao IS NULL)
          + (SELECT COUNT(*) FROM inep_escola WHERE id_ingestao IS NULL)
          + (SELECT COUNT(*) FROM inep_curso_tecnico WHERE id_ingestao IS NULL)
          + (SELECT COUNT(*) FROM mec_ies WHERE id_ingestao IS NULL)
          + (SELECT COUNT(*) FROM mec_cursos WHERE id_ingestao IS NULL)
     """, lambda n: n == 0, "ATENÇÃO"),
    ("Cargas que terminaram em FALHA (última de cada arquivo)",
     "SELECT COUNT(*) FROM vw_ultimas_cargas WHERE ds_status = 'FALHA'",
     lambda n: n == 0, "ATENÇÃO"),
    ("Cargas interrompidas (status INICIADA)",
     "SELECT COUNT(*) FROM vw_ultimas_cargas WHERE ds_status = 'INICIADA'",
     lambda n: n == 0, "ATENÇÃO"),
]


def verificar_banco() -> bool:
    print("\n=== VERIFICAÇÃO DO BANCO ===")
    sem_erro = True

    with get_engine().connect() as conexao:
        for descricao, sql, regra, nivel in VERIFICACOES:
            valor = conexao.execute(text(sql)).scalar_one()
            ok = regra(valor)
            marca = "OK     " if ok else f"{nivel:<7}"
            print(f"[{marca}] {descricao}: {valor}")

            if not ok and nivel == "ERRO":
                sem_erro = False

    print("Resultado:", "sem erros." if sem_erro else "há ERROS a corrigir.")
    return sem_erro


if __name__ == "__main__":
    raise SystemExit(0 if verificar_banco() else 1)
