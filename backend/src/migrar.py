"""Aplica as migrations SQL de backend/database/migrations, em ordem.

Cada arquivo roda numa transação única: se falhar, nada é alterado.
As migrations aplicadas ficam registradas na tabela VELTIS_MIGRACAO,
com o hash do arquivo, para nunca rodar a mesma migration duas vezes.

Uso (dentro de backend/, com o ambiente virtual ativado):

    python -m src.migrar --status
        Lista as migrations e diz quais já foram aplicadas.

    python -m src.migrar
        Aplica as migrations pendentes.

    python -m src.migrar --marcar-aplicada 001_schema_inicial.sql
        Registra uma migration como aplicada SEM executá-la.
        Use no Supabase para a 001, que já foi criada à mão.
"""

import argparse
import hashlib
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from src.database import get_engine


PASTA_MIGRATIONS = (
    Path(__file__).resolve().parents[1] / "database" / "migrations"
)

SQL_TABELA_CONTROLE = """
CREATE TABLE IF NOT EXISTS VELTIS_MIGRACAO (
    NO_ARQUIVO VARCHAR(255) PRIMARY KEY,
    DS_HASH_SHA256 CHAR(64) NOT NULL,
    DT_APLICACAO TIMESTAMP NOT NULL DEFAULT NOW(),
    DS_MODO VARCHAR(20) NOT NULL
);
ALTER TABLE VELTIS_MIGRACAO ENABLE ROW LEVEL SECURITY;
"""


def listar_arquivos() -> list[Path]:
    return sorted(PASTA_MIGRATIONS.glob("*.sql"))


def hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def migrations_aplicadas(conexao) -> dict[str, str]:
    conexao.exec_driver_sql(SQL_TABELA_CONTROLE)

    linhas = conexao.execute(
        text("SELECT no_arquivo, ds_hash_sha256 FROM veltis_migracao")
    ).all()

    return {nome: hash_ for nome, hash_ in linhas}


def registrar(conexao, caminho: Path, modo: str) -> None:
    conexao.execute(
        text(
            """
            INSERT INTO veltis_migracao (no_arquivo, ds_hash_sha256, ds_modo)
            VALUES (:nome, :hash, :modo)
            """
        ),
        {
            "nome": caminho.name,
            "hash": hash_arquivo(caminho),
            "modo": modo,
        },
    )


def mostrar_status() -> None:
    with get_engine().begin() as conexao:
        aplicadas = migrations_aplicadas(conexao)

    for caminho in listar_arquivos():
        if caminho.name not in aplicadas:
            situacao = "PENDENTE"
        elif aplicadas[caminho.name] != hash_arquivo(caminho):
            situacao = "APLICADA (arquivo alterado depois!)"
        else:
            situacao = "aplicada"

        print(f"{situacao:<38} {caminho.name}")


def marcar_aplicada(nome_arquivo: str) -> None:
    caminho = PASTA_MIGRATIONS / nome_arquivo

    if not caminho.exists():
        raise FileNotFoundError(f"Migration não encontrada: {caminho}")

    with get_engine().begin() as conexao:
        if nome_arquivo in migrations_aplicadas(conexao):
            print(f"{nome_arquivo} já estava registrada.")
            return

        registrar(conexao, caminho, "MARCADA")

    print(f"{nome_arquivo} registrada como aplicada (sem executar).")


def aplicar_pendentes() -> None:
    with get_engine().begin() as conexao:
        aplicadas = migrations_aplicadas(conexao)

    pendentes = [
        caminho
        for caminho in listar_arquivos()
        if caminho.name not in aplicadas
    ]

    if not pendentes:
        print("Nenhuma migration pendente.")
        return

    for caminho in pendentes:
        print(f"Aplicando {caminho.name}...")

        # Uma transação por arquivo: se falhar, o arquivo inteiro é desfeito.
        try:
            with get_engine().begin() as conexao:
                conexao.exec_driver_sql(caminho.read_text(encoding="utf-8"))
                registrar(conexao, caminho, "EXECUTADA")
        except DBAPIError as erro:
            mensagem = str(getattr(erro, "orig", erro)).strip()
            raise SystemExit(
                f"\nFALHA em {caminho.name}. Nada deste arquivo foi aplicado.\n"
                f"Erro do banco: {mensagem}"
            ) from None

        print(f"{caminho.name} aplicada com sucesso.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrations do Veltis")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--marcar-aplicada", metavar="ARQUIVO")
    args = parser.parse_args()

    if args.status:
        mostrar_status()
    elif args.marcar_aplicada:
        marcar_aplicada(args.marcar_aplicada)
    else:
        aplicar_pendentes()


if __name__ == "__main__":
    main()
