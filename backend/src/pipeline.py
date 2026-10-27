"""Roda todos os pipelines na ordem exigida pelas chaves estrangeiras.

    1. malha          IBGE Malha Municipal        -> ibge_municipios
    2. sidra          IBGE SIDRA                  -> ibge_demografico
    3. censo_escolar  INEP Censo Escolar          -> inep_escola, inep_curso_tecnico
    4. localizacao    Catálogo INEP + SEDUC-SP    -> escola_localizacao
    5. censo_superior INEP Censo Superior         -> mec_ies, mec_cursos

Uso (dentro de backend/, com o ambiente virtual ativado):
    python -m src.pipeline                      # tudo
    python -m src.pipeline --apenas sidra       # uma etapa
    python -m src.pipeline --forcar             # recarrega mesmo sem mudança
    python -m src.pipeline --verificar          # só o relatório do banco

Se uma etapa falhar, as seguintes não rodam (elas dependem da anterior)
e o erro fica registrado em CONTROLE_INGESTAO com status FALHA.
"""

import argparse
import sys
import time
import traceback

from src.collectors import (
    censo_escolar,
    censo_superior,
    ibge_malha,
    localizacao_escolas,
    sidra,
)
from src.verificar import verificar_banco


ETAPAS = [
    ("malha", ibge_malha.executar_pipeline),
    ("sidra", sidra.executar_pipeline),
    ("censo_escolar", censo_escolar.executar_pipeline),
    ("localizacao", localizacao_escolas.executar_pipeline),
    ("censo_superior", censo_superior.executar_pipeline),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipelines de dados do Veltis")
    parser.add_argument("--apenas", choices=[nome for nome, _ in ETAPAS])
    parser.add_argument("--forcar", action="store_true")
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()

    if args.verificar:
        return 0 if verificar_banco() else 1

    etapas = [(n, f) for n, f in ETAPAS if args.apenas in (None, n)]

    for nome, executar in etapas:
        inicio = time.monotonic()

        try:
            executar(forcar=args.forcar)
        except Exception:
            traceback.print_exc()
            print(
                f"\nETAPA '{nome}' FALHOU. As etapas seguintes não foram executadas. "
                "Veja o erro acima e a tabela controle_ingestao (status FALHA)."
            )
            return 1

        print(f"[{nome}] ok em {time.monotonic() - inicio:.0f}s")

    return 0 if verificar_banco() else 1


if __name__ == "__main__":
    sys.exit(main())
